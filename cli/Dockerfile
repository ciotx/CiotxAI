# Build all platform binaries
FROM golang:1.22-alpine AS builder

ARG API_URL=http://localhost:8000
ARG DASHBOARD_URL=http://localhost:3000

WORKDIR /app

COPY go.mod go.sum* ./
RUN go mod download

COPY . .

RUN mkdir -p /output && \
    CGO_ENABLED=0 go build \
      -ldflags="-s -w \
        -X 'github.com/ciotx/cli/internal/config.DefaultAPIURL=${API_URL}' \
        -X 'github.com/ciotx/cli/internal/config.DefaultDashboardURL=${DASHBOARD_URL}'" \
      -o /output/ciotx-linux-amd64 . && \
    CGO_ENABLED=0 GOOS=darwin GOARCH=amd64 go build \
      -ldflags="-s -w \
        -X 'github.com/ciotx/cli/internal/config.DefaultAPIURL=${API_URL}' \
        -X 'github.com/ciotx/cli/internal/config.DefaultDashboardURL=${DASHBOARD_URL}'" \
      -o /output/ciotx-darwin-amd64 . && \
    CGO_ENABLED=0 GOOS=darwin GOARCH=arm64 go build \
      -ldflags="-s -w \
        -X 'github.com/ciotx/cli/internal/config.DefaultAPIURL=${API_URL}' \
        -X 'github.com/ciotx/cli/internal/config.DefaultDashboardURL=${DASHBOARD_URL}'" \
      -o /output/ciotx-darwin-arm64 . && \
    CGO_ENABLED=0 GOOS=windows GOARCH=amd64 go build \
      -ldflags="-s -w \
        -X 'github.com/ciotx/cli/internal/config.DefaultAPIURL=${API_URL}' \
        -X 'github.com/ciotx/cli/internal/config.DefaultDashboardURL=${DASHBOARD_URL}'" \
      -o /output/ciotx-windows-amd64.exe .

# Need alpine (not scratch) so the container has a shell for the copy command
FROM alpine:3.19
COPY --from=builder /output/ /builds/
