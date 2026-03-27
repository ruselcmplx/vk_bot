FROM golang:1.25-alpine AS builder

WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /out/vk-bot ./cmd/vk-bot

FROM alpine:3.20

WORKDIR /app
RUN adduser -D -H appuser
COPY --from=builder /out/vk-bot /app/vk-bot
USER appuser

# config должен монтироваться с хоста:
#   - ./config:/app/config
CMD ["/app/vk-bot"]
