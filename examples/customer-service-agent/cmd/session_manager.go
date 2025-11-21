package main

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/go-redis/redis/v8"
)

// SessionManager handles chat session state
type SessionManager struct {
	client          *redis.Client
	maxConcurrent   int
	sessionTTL      time.Duration
}

// Session represents a chat session
type Session struct {
	SessionID   string           `json:"session_id"`
	UserID      string           `json:"user_id"`
	Channel     string           `json:"channel"`
	StartedAt   time.Time        `json:"started_at"`
	LastActivity time.Time       `json:"last_activity"`
	Messages    []SessionMessage `json:"messages"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// SessionMessage represents a message in the session
type SessionMessage struct {
	Role      string    `json:"role"` // user or assistant
	Content   string    `json:"content"`
	Timestamp time.Time `json:"timestamp"`
}

// NewSessionManager creates a new session manager
func NewSessionManager(redisURL string, maxConcurrent int) (*SessionManager, error) {
	opts, err := redis.ParseURL(redisURL)
	if err != nil {
		return nil, fmt.Errorf("invalid redis url: %w", err)
	}

	client := redis.NewClient(opts)

	// Test connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := client.Ping(ctx).Err(); err != nil {
		return nil, fmt.Errorf("redis connection failed: %w", err)
	}

	return &SessionManager{
		client:        client,
		maxConcurrent: maxConcurrent,
		sessionTTL:    24 * time.Hour, // Sessions expire after 24 hours of inactivity
	}, nil
}

// GetOrCreate retrieves an existing session or creates a new one
func (sm *SessionManager) GetOrCreate(ctx context.Context, sessionID, userID string) (*Session, error) {
	// Try to get existing session
	session, err := sm.Get(ctx, sessionID)
	if err == nil && session != nil {
		// Update last activity
		session.LastActivity = time.Now()
		if err := sm.Save(ctx, session); err != nil {
			return nil, err
		}
		return session, nil
	}

	// Check concurrent session limit
	activeCount, err := sm.GetActiveCount()
	if err != nil {
		return nil, err
	}

	if activeCount >= sm.maxConcurrent {
		return nil, fmt.Errorf("maximum concurrent sessions reached (%d)", sm.maxConcurrent)
	}

	// Create new session
	session = &Session{
		SessionID:    sessionID,
		UserID:       userID,
		StartedAt:    time.Now(),
		LastActivity: time.Now(),
		Messages:     []SessionMessage{},
		Metadata:     make(map[string]interface{}),
	}

	if err := sm.Save(ctx, session); err != nil {
		return nil, err
	}

	// Update active session counter
	activeConcurrentChats.Inc()

	return session, nil
}

// Get retrieves a session by ID
func (sm *SessionManager) Get(ctx context.Context, sessionID string) (*Session, error) {
	key := sm.sessionKey(sessionID)

	data, err := sm.client.Get(ctx, key).Bytes()
	if err == redis.Nil {
		return nil, nil
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get session: %w", err)
	}

	var session Session
	if err := json.Unmarshal(data, &session); err != nil {
		return nil, fmt.Errorf("failed to unmarshal session: %w", err)
	}

	return &session, nil
}

// Save saves a session
func (sm *SessionManager) Save(ctx context.Context, session *Session) error {
	key := sm.sessionKey(session.SessionID)

	data, err := json.Marshal(session)
	if err != nil {
		return fmt.Errorf("failed to marshal session: %w", err)
	}

	if err := sm.client.Set(ctx, key, data, sm.sessionTTL).Err(); err != nil {
		return fmt.Errorf("failed to save session: %w", err)
	}

	return nil
}

// AddMessage adds a message to the session
func (sm *SessionManager) AddMessage(ctx context.Context, sessionID, role, content string) error {
	session, err := sm.Get(ctx, sessionID)
	if err != nil {
		return err
	}
	if session == nil {
		return fmt.Errorf("session not found: %s", sessionID)
	}

	message := SessionMessage{
		Role:      role,
		Content:   content,
		Timestamp: time.Now(),
	}

	session.Messages = append(session.Messages, message)
	session.LastActivity = time.Now()

	// Limit message history to last 50 messages to avoid unbounded growth
	if len(session.Messages) > 50 {
		session.Messages = session.Messages[len(session.Messages)-50:]
	}

	return sm.Save(ctx, session)
}

// GetHistory retrieves conversation history
func (sm *SessionManager) GetHistory(ctx context.Context, sessionID string) ([]SessionMessage, error) {
	session, err := sm.Get(ctx, sessionID)
	if err != nil {
		return nil, err
	}
	if session == nil {
		return []SessionMessage{}, nil
	}

	return session.Messages, nil
}

// EndSession terminates a session
func (sm *SessionManager) EndSession(ctx context.Context, sessionID string) error {
	key := sm.sessionKey(sessionID)

	if err := sm.client.Del(ctx, key).Err(); err != nil {
		return fmt.Errorf("failed to delete session: %w", err)
	}

	return nil
}

// GetActiveCount returns the number of active sessions
func (sm *SessionManager) GetActiveCount() (int, error) {
	ctx := context.Background()

	// Count keys matching the session pattern
	keys, err := sm.client.Keys(ctx, "session:*").Result()
	if err != nil {
		return 0, err
	}

	return len(keys), nil
}

// GetActiveSessions returns all active sessions
func (sm *SessionManager) GetActiveSessions(ctx context.Context) ([]*Session, error) {
	keys, err := sm.client.Keys(ctx, "session:*").Result()
	if err != nil {
		return nil, err
	}

	sessions := make([]*Session, 0, len(keys))
	for _, key := range keys {
		data, err := sm.client.Get(ctx, key).Bytes()
		if err != nil {
			continue
		}

		var session Session
		if err := json.Unmarshal(data, &session); err != nil {
			continue
		}

		sessions = append(sessions, &session)
	}

	return sessions, nil
}

// CleanupInactive removes inactive sessions
func (sm *SessionManager) CleanupInactive(ctx context.Context, inactiveDuration time.Duration) (int, error) {
	sessions, err := sm.GetActiveSessions(ctx)
	if err != nil {
		return 0, err
	}

	cleaned := 0
	cutoff := time.Now().Add(-inactiveDuration)

	for _, session := range sessions {
		if session.LastActivity.Before(cutoff) {
			if err := sm.EndSession(ctx, session.SessionID); err != nil {
				continue
			}
			cleaned++
		}
	}

	return cleaned, nil
}

// HealthCheck checks if Redis is available
func (sm *SessionManager) HealthCheck() bool {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	err := sm.client.Ping(ctx).Err()
	return err == nil
}

// Close closes the Redis connection
func (sm *SessionManager) Close() error {
	return sm.client.Close()
}

// sessionKey generates the Redis key for a session
func (sm *SessionManager) sessionKey(sessionID string) string {
	return fmt.Sprintf("session:%s", sessionID)
}

// StartCleanupRoutine starts a background routine to clean up inactive sessions
func (sm *SessionManager) StartCleanupRoutine(interval, inactiveDuration time.Duration) {
	ticker := time.NewTicker(interval)
	go func() {
		for range ticker.C {
			ctx := context.Background()
			cleaned, err := sm.CleanupInactive(ctx, inactiveDuration)
			if err != nil {
				fmt.Printf("Session cleanup error: %v\n", err)
			} else if cleaned > 0 {
				fmt.Printf("Cleaned up %d inactive sessions\n", cleaned)
			}
		}
	}()
}
