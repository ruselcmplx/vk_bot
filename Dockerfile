FROM --platform=$BUILDPLATFORM golang:1.25-alpine AS builder

WORKDIR /src
ARG TARGETOS
ARG TARGETARCH
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=$TARGETOS GOARCH=$TARGETARCH go build -o /out/vk-bot ./cmd/vk-bot

FROM alpine:3.20

WORKDIR /app
COPY --from=builder /out/vk-bot /app/vk-bot
USER 65532:65532

# config должен монтироваться с хоста:
#   - ./config:/app/config
CMD ["/app/vk-bot"]
