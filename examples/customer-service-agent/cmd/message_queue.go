package main

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/go-redis/redis/v8"
)

// MessageQueue handles async message processing using Redis Streams
type MessageQueue struct {
	client     *redis.Client
	streamName string
	groupName  string
	maxLen     int64
}

// NewMessageQueue creates a new message queue
func NewMessageQueue(redisURL string, maxLen int) (*MessageQueue, error) {
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

	mq := &MessageQueue{
		client:     client,
		streamName: "agent_messages",
		groupName:  "workers",
		maxLen:     int64(maxLen),
	}

	// Create consumer group if it doesn't exist
	if err := mq.createConsumerGroup(); err != nil {
		return nil, err
	}

	return mq, nil
}

// createConsumerGroup creates the consumer group for the stream
func (mq *MessageQueue) createConsumerGroup() error {
	ctx := context.Background()

	// Try to create the group
	err := mq.client.XGroupCreateMkStream(ctx, mq.streamName, mq.groupName, "0").Err()
	if err != nil && err.Error() != "BUSYGROUP Consumer Group name already exists" {
		return fmt.Errorf("failed to create consumer group: %w", err)
	}

	return nil
}

// Enqueue adds a message to the queue
func (mq *MessageQueue) Enqueue(ctx context.Context, message interface{}) error {
	// Serialize message
	data, err := json.Marshal(message)
	if err != nil {
		return fmt.Errorf("failed to marshal message: %w", err)
	}

	// Determine message type
	msgType := fmt.Sprintf("%T", message)

	// Add to stream with maxlen to prevent unbounded growth
	args := &redis.XAddArgs{
		Stream: mq.streamName,
		MaxLen: mq.maxLen,
		Approx: true, // Use approximate trimming for better performance
		Values: map[string]interface{}{
			"type": msgType,
			"data": string(data),
			"ts":   time.Now().Unix(),
		},
	}

	if err := mq.client.XAdd(ctx, args).Err(); err != nil {
		return fmt.Errorf("failed to enqueue message: %w", err)
	}

	return nil
}

// Dequeue retrieves and processes a message from the queue
func (mq *MessageQueue) Dequeue(ctx context.Context) (interface{}, error) {
	// Read from stream with consumer group
	streams, err := mq.client.XReadGroup(ctx, &redis.XReadGroupArgs{
		Group:    mq.groupName,
		Consumer: "worker", // In production, use unique consumer ID
		Streams:  []string{mq.streamName, ">"},
		Count:    1,
		Block:    time.Second,
	}).Result()

	if err == redis.Nil {
		return nil, nil // No messages available
	}
	if err != nil {
		return nil, fmt.Errorf("failed to dequeue message: %w", err)
	}

	if len(streams) == 0 || len(streams[0].Messages) == 0 {
		return nil, nil
	}

	msg := streams[0].Messages[0]

	// Extract message data
	msgType, ok := msg.Values["type"].(string)
	if !ok {
		return nil, fmt.Errorf("invalid message type")
	}

	data, ok := msg.Values["data"].(string)
	if !ok {
		return nil, fmt.Errorf("invalid message data")
	}

	// Deserialize based on type
	var message interface{}
	switch msgType {
	case "*main.ZendeskWebhook":
		var webhook ZendeskWebhook
		if err := json.Unmarshal([]byte(data), &webhook); err != nil {
			return nil, fmt.Errorf("failed to unmarshal zendesk webhook: %w", err)
		}
		message = &webhook

	case "*main.SlackWebhook":
		var webhook SlackWebhook
		if err := json.Unmarshal([]byte(data), &webhook); err != nil {
			return nil, fmt.Errorf("failed to unmarshal slack webhook: %w", err)
		}
		message = &webhook

	default:
		return nil, fmt.Errorf("unknown message type: %s", msgType)
	}

	// Acknowledge message processing
	if err := mq.client.XAck(ctx, mq.streamName, mq.groupName, msg.ID).Err(); err != nil {
		return nil, fmt.Errorf("failed to ack message: %w", err)
	}

	return message, nil
}

// Depth returns the approximate queue depth
func (mq *MessageQueue) Depth() int64 {
	ctx := context.Background()

	info, err := mq.client.XInfoStream(ctx, mq.streamName).Result()
	if err != nil {
		return 0
	}

	return info.Length
}

// HealthCheck checks if the message queue is available
func (mq *MessageQueue) HealthCheck() bool {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	err := mq.client.Ping(ctx).Err()
	return err == nil
}

// Close closes the Redis connection
func (mq *MessageQueue) Close() error {
	return mq.client.Close()
}

// GetPendingCount returns the number of pending (unacknowledged) messages
func (mq *MessageQueue) GetPendingCount(ctx context.Context) (int64, error) {
	pending, err := mq.client.XPending(ctx, mq.streamName, mq.groupName).Result()
	if err != nil {
		return 0, err
	}

	return pending.Count, nil
}

// CleanupOldMessages removes messages older than the specified duration
func (mq *MessageQueue) CleanupOldMessages(ctx context.Context, maxAge time.Duration) error {
	// Calculate cutoff timestamp
	cutoff := time.Now().Add(-maxAge).Unix()
	cutoffID := fmt.Sprintf("%d-0", cutoff*1000) // Convert to stream ID format

	// Trim stream to remove old messages
	err := mq.client.XTrimMinID(ctx, mq.streamName, cutoffID).Err()
	if err != nil {
		return fmt.Errorf("failed to cleanup old messages: %w", err)
	}

	return nil
}
