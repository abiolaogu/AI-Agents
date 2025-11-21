FROM golang:1.21-alpine AS builder
WORKDIR /build
RUN apk add --no-cache git
COPY go.mod ./
RUN go mod download
COPY cmd/ ./cmd/
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags='-w -s -extldflags "-static"' \
    -o performance-profiler \
    ./cmd/main.go

FROM alpine:3.19
RUN addgroup -g 1000 appuser && adduser -D -u 1000 -G appuser appuser
WORKDIR /app
COPY --from=builder /build/performance-profiler .
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8108
HEALTHCHECK --interval=30s --timeout=3s CMD wget --spider http://localhost:8108/health || exit 1
CMD ["./performance-profiler"]
