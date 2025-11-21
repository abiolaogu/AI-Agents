package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/trace"
)

// Configuration holds all service configuration
type Configuration struct {
	Port                string
	RedisURL            string
	QdrantURL           string
	ElasticsearchURL    string
	ClaudeAPIKey        string
	ZendeskAPIKey       string
	SlackBotToken       string
	MaxConcurrentChats  int
	MessageQueueSize    int
	WorkerPoolSize      int
	EnableTracing       bool
	LogLevel            string
}

// LoadConfig loads configuration from environment
func LoadConfig() *Configuration {
	return &Configuration{
		Port:                getEnv("PORT", "8080"),
		RedisURL:            getEnv("REDIS_URL", "redis://localhost:6379"),
		QdrantURL:           getEnv("QDRANT_URL", "http://localhost:6333"),
		ElasticsearchURL:    getEnv("ELASTICSEARCH_URL", "http://localhost:9200"),
		ClaudeAPIKey:        getEnv("CLAUDE_API_KEY", ""),
		ZendeskAPIKey:       getEnv("ZENDESK_API_KEY", ""),
		SlackBotToken:       getEnv("SLACK_BOT_TOKEN", ""),
		MaxConcurrentChats:  getEnvInt("MAX_CONCURRENT_CHATS", 10000),
		MessageQueueSize:    getEnvInt("MESSAGE_QUEUE_SIZE", 100000),
		WorkerPoolSize:      getEnvInt("WORKER_POOL_SIZE", 100),
		EnableTracing:       getEnvBool("ENABLE_TRACING", true),
		LogLevel:            getEnv("LOG_LEVEL", "info"),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		var intValue int
		fmt.Sscanf(value, "%d", &intValue)
		return intValue
	}
	return defaultValue
}

func getEnvBool(key string, defaultValue bool) bool {
	if value := os.Getenv(key); value != "" {
		return value == "true"
	}
	return defaultValue
}

// Metrics for Prometheus
var (
	messagesProcessed = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "csr_messages_processed_total",
			Help: "Total number of messages processed",
		},
		[]string{"status", "channel"},
	)

	messageLatency = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "csr_message_latency_seconds",
			Help:    "Message processing latency",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"channel"},
	)

	activeConcurrentChats = prometheus.NewGauge(
		prometheus.GaugeOpts{
			Name: "csr_active_concurrent_chats",
			Help: "Number of active concurrent conversations",
		},
	)

	sentimentDistribution = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "csr_sentiment_distribution_total",
			Help: "Distribution of detected sentiment",
		},
		[]string{"sentiment"},
	)

	llmTokensUsed = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "csr_llm_tokens_used_total",
			Help: "Total LLM tokens consumed",
		},
		[]string{"type"}, // input, output
	)
)

func init() {
	// Register Prometheus metrics
	prometheus.MustRegister(messagesProcessed)
	prometheus.MustRegister(messageLatency)
	prometheus.MustRegister(activeConcurrentChats)
	prometheus.MustRegister(sentimentDistribution)
	prometheus.MustRegister(llmTokensUsed)
}

// Application is the main application struct
type Application struct {
	Config          *Configuration
	Router          *gin.Engine
	AgentService    *AgentService
	SessionManager  *SessionManager
	MessageQueue    *MessageQueue
	KnowledgeBase   *KnowledgeBase
	Tracer          trace.Tracer
	ShutdownSignal  chan os.Signal
}

// NewApplication creates a new application instance
func NewApplication(config *Configuration) (*Application, error) {
	app := &Application{
		Config:         config,
		ShutdownSignal: make(chan os.Signal, 1),
	}

	// Initialize tracing if enabled
	if config.EnableTracing {
		app.Tracer = otel.Tracer("csr-agent")
	}

	// Initialize Redis session manager
	sessionMgr, err := NewSessionManager(config.RedisURL, config.MaxConcurrentChats)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize session manager: %w", err)
	}
	app.SessionManager = sessionMgr

	// Initialize knowledge base
	kb, err := NewKnowledgeBase(config.ElasticsearchURL)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize knowledge base: %w", err)
	}
	app.KnowledgeBase = kb

	// Initialize message queue
	queue, err := NewMessageQueue(config.RedisURL, config.MessageQueueSize)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize message queue: %w", err)
	}
	app.MessageQueue = queue

	// Initialize agent service
	agentConfig := &AgentConfig{
		ClaudeAPIKey: config.ClaudeAPIKey,
		Model:        "claude-3-5-sonnet-20241022",
		MaxTokens:    4000,
		Temperature:  0.7,
		Streaming:    true,
	}
	agentService, err := NewAgentService(agentConfig, sessionMgr, kb)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize agent service: %w", err)
	}
	app.AgentService = agentService

	// Initialize HTTP router
	app.setupRouter()

	return app, nil
}

// setupRouter configures HTTP routes
func (app *Application) setupRouter() {
	if app.Config.LogLevel == "debug" {
		gin.SetMode(gin.DebugMode)
	} else {
		gin.SetMode(gin.ReleaseMode)
	}

	router := gin.Default()

	// Health check endpoint
	router.GET("/health", app.healthCheck)
	router.GET("/ready", app.readinessCheck)

	// Metrics endpoint
	router.GET("/metrics", gin.WrapH(promhttp.Handler()))

	// API endpoints
	api := router.Group("/api/v1")
	{
		// Chat endpoints
		api.POST("/chat", app.handleChatMessage)
		api.GET("/chat/:session_id", app.getChatHistory)
		api.DELETE("/chat/:session_id", app.endChatSession)

		// Webhook endpoints
		api.POST("/webhooks/zendesk", app.handleZendeskWebhook)
		api.POST("/webhooks/slack", app.handleSlackWebhook)

		// Admin endpoints
		admin := api.Group("/admin")
		admin.Use(authMiddleware(app.Config)) // Add authentication
		{
			admin.GET("/stats", app.getStatistics)
			admin.POST("/knowledge-base/index", app.indexKnowledgeBase)
			admin.GET("/sessions/active", app.getActiveSessions)
		}
	}

	app.Router = router
}

// healthCheck returns service health
func (app *Application) healthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":  "healthy",
		"service": "csr-agent",
		"version": "2.0.0",
		"uptime":  time.Since(startTime).Seconds(),
	})
}

// readinessCheck returns service readiness
func (app *Application) readinessCheck(c *gin.Context) {
	// Check dependencies
	checks := map[string]bool{
		"redis":         app.SessionManager.HealthCheck(),
		"elasticsearch": app.KnowledgeBase.HealthCheck(),
		"message_queue": app.MessageQueue.HealthCheck(),
	}

	allHealthy := true
	for _, healthy := range checks {
		if !healthy {
			allHealthy = false
			break
		}
	}

	status := http.StatusOK
	if !allHealthy {
		status = http.StatusServiceUnavailable
	}

	c.JSON(status, gin.H{
		"ready":  allHealthy,
		"checks": checks,
	})
}

// handleChatMessage processes incoming chat messages
func (app *Application) handleChatMessage(c *gin.Context) {
	var req ChatMessageRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request"})
		return
	}

	// Validate input
	if err := req.Validate(); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Start tracing span
	ctx := c.Request.Context()
	if app.Config.EnableTracing {
		var span trace.Span
		ctx, span = app.Tracer.Start(ctx, "handle_chat_message")
		defer span.End()
	}

	// Process message
	startTime := time.Now()
	response, err := app.AgentService.ProcessMessage(ctx, &req)
	duration := time.Since(startTime).Seconds()

	// Record metrics
	messageLatency.WithLabelValues(req.Channel).Observe(duration)

	if err != nil {
		messagesProcessed.WithLabelValues("error", req.Channel).Inc()
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	messagesProcessed.WithLabelValues("success", req.Channel).Inc()
	sentimentDistribution.WithLabelValues(response.Sentiment).Inc()

	c.JSON(http.StatusOK, response)
}

// getChatHistory retrieves conversation history
func (app *Application) getChatHistory(c *gin.Context) {
	sessionID := c.Param("session_id")

	history, err := app.SessionManager.GetHistory(c.Request.Context(), sessionID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"session_id": sessionID,
		"history":    history,
	})
}

// endChatSession terminates a chat session
func (app *Application) endChatSession(c *gin.Context) {
	sessionID := c.Param("session_id")

	if err := app.SessionManager.EndSession(c.Request.Context(), sessionID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	activeConcurrentChats.Dec()

	c.JSON(http.StatusOK, gin.H{
		"message": "session ended",
		"session_id": sessionID,
	})
}

// handleZendeskWebhook processes Zendesk webhooks
func (app *Application) handleZendeskWebhook(c *gin.Context) {
	var webhook ZendeskWebhook
	if err := c.ShouldBindJSON(&webhook); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid webhook"})
		return
	}

	// Enqueue for async processing
	if err := app.MessageQueue.Enqueue(c.Request.Context(), &webhook); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusAccepted, gin.H{"status": "queued"})
}

// handleSlackWebhook processes Slack webhooks
func (app *Application) handleSlackWebhook(c *gin.Context) {
	var webhook SlackWebhook
	if err := c.ShouldBindJSON(&webhook); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid webhook"})
		return
	}

	// Handle Slack challenge for verification
	if webhook.Challenge != "" {
		c.JSON(http.StatusOK, gin.H{"challenge": webhook.Challenge})
		return
	}

	// Enqueue for async processing
	if err := app.MessageQueue.Enqueue(c.Request.Context(), &webhook); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "queued"})
}

// getStatistics returns system statistics
func (app *Application) getStatistics(c *gin.Context) {
	stats := map[string]interface{}{
		"active_sessions":    app.SessionManager.GetActiveCount(),
		"messages_processed": messagesProcessed,
		"queue_depth":        app.MessageQueue.Depth(),
		"uptime_seconds":     time.Since(startTime).Seconds(),
	}

	c.JSON(http.StatusOK, stats)
}

// indexKnowledgeBase rebuilds the knowledge base index
func (app *Application) indexKnowledgeBase(c *gin.Context) {
	if err := app.KnowledgeBase.RebuildIndex(c.Request.Context()); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "index rebuilt"})
}

// getActiveSessions returns all active sessions
func (app *Application) getActiveSessions(c *gin.Context) {
	sessions, err := app.SessionManager.GetActiveSessions(c.Request.Context())
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"count":    len(sessions),
		"sessions": sessions,
	})
}

// Start starts the application
func (app *Application) Start() error {
	// Start worker pool
	log.Printf("Starting %d workers...", app.Config.WorkerPoolSize)
	for i := 0; i < app.Config.WorkerPoolSize; i++ {
		go app.worker(i)
	}

	// Start HTTP server
	log.Printf("Starting HTTP server on port %s...", app.Config.Port)
	srv := &http.Server{
		Addr:         ":" + app.Config.Port,
		Handler:      app.Router,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  120 * time.Second,
	}

	// Handle graceful shutdown
	signal.Notify(app.ShutdownSignal, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-app.ShutdownSignal
		log.Println("Shutting down gracefully...")

		ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		defer cancel()

		if err := srv.Shutdown(ctx); err != nil {
			log.Printf("Server shutdown error: %v", err)
		}

		// Close connections
		app.SessionManager.Close()
		app.MessageQueue.Close()
		app.KnowledgeBase.Close()
	}()

	return srv.ListenAndServe()
}

// worker processes messages from the queue
func (app *Application) worker(id int) {
	log.Printf("Worker %d started", id)

	for {
		ctx := context.Background()
		message, err := app.MessageQueue.Dequeue(ctx)
		if err != nil {
			log.Printf("Worker %d: dequeue error: %v", id, err)
			time.Sleep(1 * time.Second)
			continue
		}

		if message == nil {
			time.Sleep(100 * time.Millisecond)
			continue
		}

		// Process message based on type
		if err := app.processQueuedMessage(ctx, message); err != nil {
			log.Printf("Worker %d: processing error: %v", id, err)
		}
	}
}

// processQueuedMessage processes a message from the queue
func (app *Application) processQueuedMessage(ctx context.Context, message interface{}) error {
	switch msg := message.(type) {
	case *ZendeskWebhook:
		return app.processZendeskMessage(ctx, msg)
	case *SlackWebhook:
		return app.processSlackMessage(ctx, msg)
	default:
		return fmt.Errorf("unknown message type: %T", message)
	}
}

// processZendeskMessage processes Zendesk ticket updates
func (app *Application) processZendeskMessage(ctx context.Context, webhook *ZendeskWebhook) error {
	// Convert to chat message
	req := &ChatMessageRequest{
		SessionID: fmt.Sprintf("zendesk-%d", webhook.TicketID),
		Message:   webhook.Comment,
		UserID:    webhook.RequesterID,
		Channel:   "zendesk",
		Metadata: map[string]interface{}{
			"ticket_id": webhook.TicketID,
			"priority":  webhook.Priority,
		},
	}

	// Process with agent
	response, err := app.AgentService.ProcessMessage(ctx, req)
	if err != nil {
		return err
	}

	// Send response back to Zendesk
	return app.sendZendeskResponse(ctx, webhook.TicketID, response.Message)
}

// processSlackMessage processes Slack messages
func (app *Application) processSlackMessage(ctx context.Context, webhook *SlackWebhook) error {
	// Implement Slack message processing
	// Similar to Zendesk but with Slack API
	return nil
}

// sendZendeskResponse sends a response to Zendesk
func (app *Application) sendZendeskResponse(ctx context.Context, ticketID int, message string) error {
	// Implement Zendesk API call to add comment
	// This is a placeholder
	log.Printf("Sending to Zendesk ticket %d: %s", ticketID, message)
	return nil
}

// authMiddleware provides API authentication
func authMiddleware(config *Configuration) gin.HandlerFunc {
	return func(c *gin.Context) {
		apiKey := c.GetHeader("X-API-Key")
		if apiKey == "" || apiKey != os.Getenv("API_KEY") {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
			c.Abort()
			return
		}
		c.Next()
	}
}

var startTime = time.Now()

func main() {
	log.Println("Starting Customer Service Representative Agent...")

	// Load configuration
	config := LoadConfig()

	// Validate required configuration
	if config.ClaudeAPIKey == "" {
		log.Fatal("CLAUDE_API_KEY environment variable is required")
	}

	// Create application
	app, err := NewApplication(config)
	if err != nil {
		log.Fatalf("Failed to create application: %v", err)
	}

	log.Printf("Configuration loaded:")
	log.Printf("  - Port: %s", config.Port)
	log.Printf("  - Max Concurrent Chats: %d", config.MaxConcurrentChats)
	log.Printf("  - Worker Pool Size: %d", config.WorkerPoolSize)
	log.Printf("  - Tracing Enabled: %v", config.EnableTracing)

	// Start application
	if err := app.Start(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("Server error: %v", err)
	}

	log.Println("Server stopped gracefully")
}
