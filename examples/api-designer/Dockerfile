FROM rust:1.75-alpine AS builder
WORKDIR /build
RUN apk add --no-cache musl-dev
COPY Cargo.toml ./
COPY src/ ./src/
RUN cargo build --release

FROM alpine:3.19
RUN addgroup -g 1000 appuser && adduser -D -u 1000 -G appuser appuser
WORKDIR /app
COPY --from=builder /build/target/release/api-designer .
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8106
HEALTHCHECK --interval=30s --timeout=3s CMD wget --spider http://localhost:8106/health || exit 1
CMD ["./api-designer"]
