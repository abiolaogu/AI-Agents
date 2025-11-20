package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

// KnowledgeBase handles Elasticsearch operations
type KnowledgeBase struct {
	url        string
	indexName  string
	httpClient *http.Client
}

// NewKnowledgeBase creates a new knowledge base instance
func NewKnowledgeBase(elasticsearchURL string) (*KnowledgeBase, error) {
	kb := &KnowledgeBase{
		url:       elasticsearchURL,
		indexName: "kb_articles",
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}

	// Create index if it doesn't exist
	if err := kb.createIndex(); err != nil {
		return nil, err
	}

	return kb, nil
}

// createIndex creates the Elasticsearch index with mapping
func (kb *KnowledgeBase) createIndex() error {
	mapping := map[string]interface{}{
		"mappings": map[string]interface{}{
			"properties": map[string]interface{}{
				"id": map[string]string{
					"type": "keyword",
				},
				"title": map[string]interface{}{
					"type": "text",
					"fields": map[string]interface{}{
						"keyword": map[string]string{
							"type": "keyword",
						},
					},
				},
				"content": map[string]interface{}{
					"type": "text",
					"analyzer": "english",
				},
				"category": map[string]string{
					"type": "keyword",
				},
				"tags": map[string]string{
					"type": "keyword",
				},
				"url": map[string]string{
					"type": "keyword",
				},
				"created_at": map[string]string{
					"type": "date",
				},
				"updated_at": map[string]string{
					"type": "date",
				},
				"view_count": map[string]string{
					"type": "integer",
				},
			},
		},
		"settings": map[string]interface{}{
			"number_of_shards":   3,
			"number_of_replicas": 1,
		},
	}

	jsonData, _ := json.Marshal(mapping)

	req, err := http.NewRequest("PUT", fmt.Sprintf("%s/%s", kb.url, kb.indexName), bytes.NewBuffer(jsonData))
	if err != nil {
		return err
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := kb.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	// Index might already exist (409), which is OK
	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusBadRequest {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("failed to create index (status %d): %s", resp.StatusCode, string(body))
	}

	return nil
}

// Search searches the knowledge base
func (kb *KnowledgeBase) Search(ctx context.Context, query string, limit int) ([]KBArticle, error) {
	// Build Elasticsearch query
	searchQuery := map[string]interface{}{
		"query": map[string]interface{}{
			"multi_match": map[string]interface{}{
				"query":  query,
				"fields": []string{"title^3", "content^1", "tags^2"},
				"type":   "best_fields",
			},
		},
		"size": limit,
		"_source": []string{"id", "title", "content", "url"},
	}

	jsonData, _ := json.Marshal(searchQuery)

	req, err := http.NewRequestWithContext(ctx, "POST",
		fmt.Sprintf("%s/%s/_search", kb.url, kb.indexName),
		bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, err
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := kb.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("search failed (status %d): %s", resp.StatusCode, string(body))
	}

	var searchResp ElasticsearchResponse
	if err := json.NewDecoder(resp.Body).Decode(&searchResp); err != nil {
		return nil, err
	}

	// Convert to KBArticles
	articles := make([]KBArticle, 0, len(searchResp.Hits.Hits))
	for _, hit := range searchResp.Hits.Hits {
		article := KBArticle{
			ID:      hit.Source.ID,
			Title:   hit.Source.Title,
			Content: truncateContent(hit.Source.Content, 500),
			URL:     hit.Source.URL,
			Score:   hit.Score,
		}
		articles = append(articles, article)
	}

	return articles, nil
}

// truncateContent truncates content to specified length
func truncateContent(content string, maxLen int) string {
	if len(content) <= maxLen {
		return content
	}
	return content[:maxLen] + "..."
}

// Index adds or updates a document in the knowledge base
func (kb *KnowledgeBase) Index(ctx context.Context, article *KBArticleDocument) error {
	jsonData, err := json.Marshal(article)
	if err != nil {
		return err
	}

	req, err := http.NewRequestWithContext(ctx, "PUT",
		fmt.Sprintf("%s/%s/_doc/%s", kb.url, kb.indexName, article.ID),
		bytes.NewBuffer(jsonData))
	if err != nil {
		return err
	}

	req.Header.Set("Content-Type", "application/json")

	resp, err := kb.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("index failed (status %d): %s", resp.StatusCode, string(body))
	}

	return nil
}

// BulkIndex indexes multiple documents at once
func (kb *KnowledgeBase) BulkIndex(ctx context.Context, articles []KBArticleDocument) error {
	if len(articles) == 0 {
		return nil
	}

	// Build bulk request body
	var bulkBody strings.Builder
	for _, article := range articles {
		// Action line
		action := map[string]interface{}{
			"index": map[string]string{
				"_index": kb.indexName,
				"_id":    article.ID,
			},
		}
		actionJSON, _ := json.Marshal(action)
		bulkBody.Write(actionJSON)
		bulkBody.WriteString("\n")

		// Document line
		docJSON, _ := json.Marshal(article)
		bulkBody.Write(docJSON)
		bulkBody.WriteString("\n")
	}

	req, err := http.NewRequestWithContext(ctx, "POST",
		fmt.Sprintf("%s/_bulk", kb.url),
		strings.NewReader(bulkBody.String()))
	if err != nil {
		return err
	}

	req.Header.Set("Content-Type", "application/x-ndjson")

	resp, err := kb.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("bulk index failed (status %d): %s", resp.StatusCode, string(body))
	}

	return nil
}

// RebuildIndex rebuilds the entire knowledge base index
func (kb *KnowledgeBase) RebuildIndex(ctx context.Context) error {
	// In a real implementation, this would:
	// 1. Fetch all articles from source system (CMS, database, etc.)
	// 2. Delete and recreate the index
	// 3. Bulk index all articles

	// For this example, we'll just create sample data
	sampleArticles := []KBArticleDocument{
		{
			ID:        "kb-001",
			Title:     "How to Reset Your Password",
			Content:   "To reset your password, go to the login page and click 'Forgot Password'. Enter your email address and follow the instructions sent to your inbox.",
			Category:  "account",
			Tags:      []string{"password", "security", "login"},
			URL:       "https://support.example.com/kb/reset-password",
			CreatedAt: time.Now().Add(-30 * 24 * time.Hour),
			UpdatedAt: time.Now().Add(-5 * 24 * time.Hour),
			ViewCount: 1250,
		},
		{
			ID:        "kb-002",
			Title:     "Shipping and Delivery Information",
			Content:   "Standard shipping takes 5-7 business days. Express shipping is available for 2-3 day delivery. Free shipping on orders over $50.",
			Category:  "shipping",
			Tags:      []string{"shipping", "delivery", "orders"},
			URL:       "https://support.example.com/kb/shipping-info",
			CreatedAt: time.Now().Add(-60 * 24 * time.Hour),
			UpdatedAt: time.Now().Add(-10 * 24 * time.Hour),
			ViewCount: 3420,
		},
		{
			ID:        "kb-003",
			Title:     "Return and Refund Policy",
			Content:   "You can return items within 30 days of purchase for a full refund. Items must be unused and in original packaging. Refunds are processed within 5-7 business days.",
			Category:  "returns",
			Tags:      []string{"returns", "refunds", "policy"},
			URL:       "https://support.example.com/kb/return-policy",
			CreatedAt: time.Now().Add(-90 * 24 * time.Hour),
			UpdatedAt: time.Now().Add(-2 * 24 * time.Hour),
			ViewCount: 2180,
		},
		{
			ID:        "kb-004",
			Title:     "How to Track Your Order",
			Content:   "Once your order ships, you'll receive a tracking number via email. Use this number on our tracking page or the carrier's website to see real-time updates.",
			Category:  "orders",
			Tags:      []string{"tracking", "orders", "shipping"},
			URL:       "https://support.example.com/kb/track-order",
			CreatedAt: time.Now().Add(-45 * 24 * time.Hour),
			UpdatedAt: time.Now().Add(-7 * 24 * time.Hour),
			ViewCount: 5670,
		},
		{
			ID:        "kb-005",
			Title:     "Payment Methods Accepted",
			Content:   "We accept Visa, Mastercard, American Express, PayPal, and Apple Pay. All transactions are encrypted and secure.",
			Category:  "billing",
			Tags:      []string{"payment", "billing", "security"},
			URL:       "https://support.example.com/kb/payment-methods",
			CreatedAt: time.Now().Add(-20 * 24 * time.Hour),
			UpdatedAt: time.Now().Add(-3 * 24 * time.Hour),
			ViewCount: 890,
		},
	}

	return kb.BulkIndex(ctx, sampleArticles)
}

// HealthCheck checks if Elasticsearch is available
func (kb *KnowledgeBase) HealthCheck() bool {
	resp, err := kb.httpClient.Get(fmt.Sprintf("%s/_cluster/health", kb.url))
	if err != nil {
		return false
	}
	defer resp.Body.Close()

	return resp.StatusCode == http.StatusOK
}

// Close closes the knowledge base (placeholder for cleanup)
func (kb *KnowledgeBase) Close() error {
	// No cleanup needed for HTTP client
	return nil
}

// KBArticleDocument represents a knowledge base article for indexing
type KBArticleDocument struct {
	ID        string    `json:"id"`
	Title     string    `json:"title"`
	Content   string    `json:"content"`
	Category  string    `json:"category"`
	Tags      []string  `json:"tags"`
	URL       string    `json:"url"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
	ViewCount int       `json:"view_count"`
}

// ElasticsearchResponse represents the search response from Elasticsearch
type ElasticsearchResponse struct {
	Hits struct {
		Total struct {
			Value int `json:"value"`
		} `json:"total"`
		Hits []struct {
			Source KBArticleDocument `json:"_source"`
			Score  float64           `json:"_score"`
		} `json:"hits"`
	} `json:"hits"`
}
