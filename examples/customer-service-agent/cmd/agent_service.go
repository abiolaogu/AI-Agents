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

// AgentConfig contains configuration for the agent service
type AgentConfig struct {
	ClaudeAPIKey string
	Model        string
	MaxTokens    int
	Temperature  float64
	Streaming    bool
}

// AgentService handles AI agent operations
type AgentService struct {
	config         *AgentConfig
	sessionManager *SessionManager
	knowledgeBase  *KnowledgeBase
	httpClient     *http.Client
	systemPrompt   string
}

// NewAgentService creates a new agent service
func NewAgentService(config *AgentConfig, sessionMgr *SessionManager, kb *KnowledgeBase) (*AgentService, error) {
	return &AgentService{
		config:         config,
		sessionManager: sessionMgr,
		knowledgeBase:  kb,
		httpClient: &http.Client{
			Timeout: 60 * time.Second,
		},
		systemPrompt: buildSystemPrompt(),
	}, nil
}

// buildSystemPrompt creates the system prompt for the customer service agent
func buildSystemPrompt() string {
	return `You are an expert customer service representative AI assistant. Your role is to:

1. **Understand Customer Intent**: Carefully analyze what the customer needs
2. **Show Empathy**: Acknowledge frustrations and show understanding
3. **Provide Solutions**: Offer clear, actionable solutions
4. **Be Concise**: Keep responses focused and easy to understand
5. **Know When to Escalate**: Identify issues requiring human intervention

**Guidelines**:
- Always be polite, professional, and friendly
- Use the customer's name when appropriate
- Apologize for issues and take ownership
- Provide specific next steps
- Ask clarifying questions when needed
- Never make promises you can't keep
- If unsure, offer to escalate to a specialist

**Response Format**:
- Keep initial responses under 100 words
- Use bullet points for multiple steps
- Include relevant links or resources
- End with a clear next action

**Sentiment Awareness**:
- Detect customer emotion (happy, neutral, frustrated, angry)
- Adjust tone accordingly
- Prioritize urgent issues
- Offer proactive solutions for negative sentiment

**Knowledge Base**:
- Search the knowledge base for relevant articles
- Cite sources when providing information
- Verify accuracy before responding

You have access to these tools:
- search_knowledge_base(query): Search for relevant KB articles
- escalate_to_human(reason, priority): Escalate to human agent
- get_order_status(order_id): Get order status
- process_refund(order_id, reason): Process refund requests
- update_ticket_priority(ticket_id, priority): Change ticket priority`
}

// ChatMessageRequest represents an incoming message
type ChatMessageRequest struct {
	SessionID string                 `json:"session_id" binding:"required"`
	Message   string                 `json:"message" binding:"required"`
	UserID    string                 `json:"user_id" binding:"required"`
	Channel   string                 `json:"channel"` // slack, zendesk, web, etc.
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
}

// Validate validates the chat message request
func (r *ChatMessageRequest) Validate() error {
	if r.SessionID == "" {
		return fmt.Errorf("session_id is required")
	}
	if r.Message == "" {
		return fmt.Errorf("message is required")
	}
	if r.UserID == "" {
		return fmt.Errorf("user_id is required")
	}
	if len(r.Message) > 4000 {
		return fmt.Errorf("message too long (max 4000 characters)")
	}
	return nil
}

// ChatMessageResponse represents the agent's response
type ChatMessageResponse struct {
	SessionID     string                 `json:"session_id"`
	Message       string                 `json:"message"`
	Sentiment     string                 `json:"sentiment"` // positive, neutral, negative, urgent
	Confidence    float64                `json:"confidence"`
	ShouldEscalate bool                  `json:"should_escalate"`
	SuggestedActions []string            `json:"suggested_actions,omitempty"`
	KBArticles    []KBArticle            `json:"kb_articles,omitempty"`
	Metadata      map[string]interface{} `json:"metadata,omitempty"`
	TokensUsed    TokenUsage             `json:"tokens_used"`
	ProcessingTime float64               `json:"processing_time_ms"`
}

// TokenUsage tracks LLM token consumption
type TokenUsage struct {
	InputTokens  int `json:"input_tokens"`
	OutputTokens int `json:"output_tokens"`
	TotalTokens  int `json:"total_tokens"`
}

// KBArticle represents a knowledge base article
type KBArticle struct {
	ID      string  `json:"id"`
	Title   string  `json:"title"`
	Content string  `json:"content"`
	URL     string  `json:"url"`
	Score   float64 `json:"relevance_score"`
}

// ProcessMessage processes an incoming message through the AI agent
func (s *AgentService) ProcessMessage(ctx context.Context, req *ChatMessageRequest) (*ChatMessageResponse, error) {
	startTime := time.Now()

	// Get or create session
	session, err := s.sessionManager.GetOrCreate(ctx, req.SessionID, req.UserID)
	if err != nil {
		return nil, fmt.Errorf("session management error: %w", err)
	}

	// Analyze sentiment
	sentiment := s.analyzeSentiment(req.Message)

	// Search knowledge base for relevant articles
	kbArticles, err := s.searchKnowledgeBase(ctx, req.Message)
	if err != nil {
		// Log error but don't fail the request
		fmt.Printf("Knowledge base search error: %v\n", err)
		kbArticles = []KBArticle{}
	}

	// Build context for Claude
	context := s.buildContext(session, req, kbArticles)

	// Call Claude API
	claudeResponse, err := s.callClaude(ctx, context)
	if err != nil {
		return nil, fmt.Errorf("claude api error: %w", err)
	}

	// Parse response and extract actions
	message, actions, shouldEscalate := s.parseResponse(claudeResponse)

	// Update session history
	if err := s.sessionManager.AddMessage(ctx, req.SessionID, "user", req.Message); err != nil {
		return nil, err
	}
	if err := s.sessionManager.AddMessage(ctx, req.SessionID, "assistant", message); err != nil {
		return nil, err
	}

	// Record metrics
	llmTokensUsed.WithLabelValues("input").Add(float64(claudeResponse.Usage.InputTokens))
	llmTokensUsed.WithLabelValues("output").Add(float64(claudeResponse.Usage.OutputTokens))

	processingTime := time.Since(startTime).Milliseconds()

	return &ChatMessageResponse{
		SessionID:      req.SessionID,
		Message:        message,
		Sentiment:      sentiment,
		Confidence:     claudeResponse.Confidence,
		ShouldEscalate: shouldEscalate,
		SuggestedActions: actions,
		KBArticles:     kbArticles,
		TokensUsed: TokenUsage{
			InputTokens:  claudeResponse.Usage.InputTokens,
			OutputTokens: claudeResponse.Usage.OutputTokens,
			TotalTokens:  claudeResponse.Usage.InputTokens + claudeResponse.Usage.OutputTokens,
		},
		ProcessingTime: float64(processingTime),
	}, nil
}

// analyzeSentiment performs simple sentiment analysis on the message
func (s *AgentService) analyzeSentiment(message string) string {
	message = strings.ToLower(message)

	// Urgent keywords
	urgentKeywords := []string{"urgent", "emergency", "critical", "asap", "immediately", "broken", "not working"}
	for _, keyword := range urgentKeywords {
		if strings.Contains(message, keyword) {
			return "urgent"
		}
	}

	// Negative keywords
	negativeKeywords := []string{"angry", "frustrated", "disappointed", "terrible", "awful", "worst", "horrible", "hate", "problem", "issue", "error", "failed"}
	negativeCount := 0
	for _, keyword := range negativeKeywords {
		if strings.Contains(message, keyword) {
			negativeCount++
		}
	}
	if negativeCount >= 2 {
		return "negative"
	}

	// Positive keywords
	positiveKeywords := []string{"thank", "thanks", "great", "excellent", "perfect", "amazing", "love", "appreciate"}
	for _, keyword := range positiveKeywords {
		if strings.Contains(message, keyword) {
			return "positive"
		}
	}

	return "neutral"
}

// searchKnowledgeBase searches for relevant KB articles
func (s *AgentService) searchKnowledgeBase(ctx context.Context, query string) ([]KBArticle, error) {
	return s.knowledgeBase.Search(ctx, query, 5)
}

// buildContext builds the conversation context for Claude
func (s *AgentService) buildContext(session *Session, req *ChatMessageRequest, kbArticles []KBArticle) []ClaudeMessage {
	messages := []ClaudeMessage{}

	// Add conversation history
	for _, msg := range session.Messages {
		messages = append(messages, ClaudeMessage{
			Role:    msg.Role,
			Content: msg.Content,
		})
	}

	// Build enhanced user message with context
	userContent := req.Message

	// Add knowledge base context if available
	if len(kbArticles) > 0 {
		kbContext := "\n\n**Relevant Knowledge Base Articles:**\n"
		for _, article := range kbArticles {
			kbContext += fmt.Sprintf("- %s (Relevance: %.2f): %s\n", article.Title, article.Score, article.Content)
		}
		userContent += kbContext
	}

	// Add current message
	messages = append(messages, ClaudeMessage{
		Role:    "user",
		Content: userContent,
	})

	return messages
}

// ClaudeMessage represents a message in Claude's format
type ClaudeMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// ClaudeRequest represents a request to Claude API
type ClaudeRequest struct {
	Model       string          `json:"model"`
	MaxTokens   int             `json:"max_tokens"`
	Temperature float64         `json:"temperature"`
	System      string          `json:"system"`
	Messages    []ClaudeMessage `json:"messages"`
	Stream      bool            `json:"stream"`
}

// ClaudeResponse represents Claude's response
type ClaudeResponse struct {
	ID      string `json:"id"`
	Type    string `json:"type"`
	Role    string `json:"role"`
	Content []struct {
		Type string `json:"type"`
		Text string `json:"text"`
	} `json:"content"`
	Model      string  `json:"model"`
	StopReason string  `json:"stop_reason"`
	Confidence float64 `json:"-"` // Calculated
	Usage      struct {
		InputTokens  int `json:"input_tokens"`
		OutputTokens int `json:"output_tokens"`
	} `json:"usage"`
}

// callClaude makes an API call to Claude
func (s *AgentService) callClaude(ctx context.Context, messages []ClaudeMessage) (*ClaudeResponse, error) {
	reqBody := ClaudeRequest{
		Model:       s.config.Model,
		MaxTokens:   s.config.MaxTokens,
		Temperature: s.config.Temperature,
		System:      s.systemPrompt,
		Messages:    messages,
		Stream:      false, // For simplicity, not using streaming in this example
	}

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", "https://api.anthropic.com/v1/messages", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-API-Key", s.config.ClaudeAPIKey)
	req.Header.Set("anthropic-version", "2023-06-01")

	resp, err := s.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to call claude api: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("claude api error (status %d): %s", resp.StatusCode, string(body))
	}

	var claudeResp ClaudeResponse
	if err := json.NewDecoder(resp.Body).Decode(&claudeResp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	// Calculate confidence based on stop reason and response quality
	claudeResp.Confidence = s.calculateConfidence(&claudeResp)

	return &claudeResp, nil
}

// calculateConfidence calculates confidence score for the response
func (s *AgentService) calculateConfidence(resp *ClaudeResponse) float64 {
	// Start with base confidence
	confidence := 0.8

	// Adjust based on stop reason
	switch resp.StopReason {
	case "end_turn":
		confidence += 0.15
	case "max_tokens":
		confidence -= 0.2
	case "stop_sequence":
		confidence += 0.05
	}

	// Ensure confidence is between 0 and 1
	if confidence > 1.0 {
		confidence = 1.0
	}
	if confidence < 0.0 {
		confidence = 0.0
	}

	return confidence
}

// parseResponse extracts message, actions, and escalation flag from Claude's response
func (s *AgentService) parseResponse(resp *ClaudeResponse) (string, []string, bool) {
	if len(resp.Content) == 0 {
		return "I apologize, but I'm having trouble processing your request. Let me escalate this to a human agent.", []string{}, true
	}

	message := resp.Content[0].Text
	actions := []string{}
	shouldEscalate := false

	// Check for escalation keywords in response
	escalationKeywords := []string{"escalate", "human agent", "specialist", "supervisor"}
	lowerMessage := strings.ToLower(message)
	for _, keyword := range escalationKeywords {
		if strings.Contains(lowerMessage, keyword) {
			shouldEscalate = true
			break
		}
	}

	// Extract suggested actions (simple pattern matching)
	// In production, this would use more sophisticated parsing
	if strings.Contains(message, "Next steps:") || strings.Contains(message, "You can:") {
		// Extract bullet points as actions
		lines := strings.Split(message, "\n")
		for _, line := range lines {
			if strings.HasPrefix(strings.TrimSpace(line), "-") || strings.HasPrefix(strings.TrimSpace(line), "•") {
				action := strings.TrimSpace(strings.TrimPrefix(strings.TrimPrefix(line, "-"), "•"))
				if action != "" {
					actions = append(actions, action)
				}
			}
		}
	}

	return message, actions, shouldEscalate
}

// ZendeskWebhook represents a Zendesk webhook payload
type ZendeskWebhook struct {
	TicketID    int    `json:"ticket_id"`
	RequesterID string `json:"requester_id"`
	Comment     string `json:"comment"`
	Priority    string `json:"priority"`
	Status      string `json:"status"`
}

// SlackWebhook represents a Slack webhook payload
type SlackWebhook struct {
	Type      string `json:"type"`
	Challenge string `json:"challenge,omitempty"` // For verification
	Event     struct {
		Type    string `json:"type"`
		Channel string `json:"channel"`
		User    string `json:"user"`
		Text    string `json:"text"`
		TS      string `json:"ts"`
	} `json:"event"`
}
