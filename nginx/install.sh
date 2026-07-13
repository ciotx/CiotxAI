#!/bin/sh
set -e

# CIOTX CLI Installer Script
# Auto-detects OS/Arch and downloads the compiled binary.

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "${BLUE}Downloading CIOTX CLI...${NC}"

# Detect OS
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

# Normalize architecture names
case "$ARCH" in
    x86_64|amd64)
        ARCH="amd64"
        ;;
    arm64|aarch64)
        ARCH="arm64"
        ;;
    *)
        echo "${RED}Unsupported architecture: $ARCH${NC}"
        exit 1
        ;;
esac

# Construct binary name
case "$OS" in
    linux)
        BINARY="ciotx-linux-amd64"
        ;;
    darwin)
        if [ "$ARCH" = "arm64" ]; then
            BINARY="ciotx-darwin-arm64"
        else
            BINARY="ciotx-darwin-amd64"
        fi
        ;;
    *)
        echo "${RED}Unsupported OS: $OS. If on Windows, download from the web interface.${NC}"
        exit 1
        ;;
esac

# Get current script host URL (defaults to orsu.space if run raw)
HOST="orsu.space"

# Download binary
TEMP_DIR="$(mktemp -d)"
echo "Downloading $BINARY from https://$HOST/bin/$BINARY..."
if ! curl -fsSL "https://$HOST/bin/$BINARY" -o "$TEMP_DIR/ciotx"; then
    # Fallback to HTTP if SSL is not configured yet
    echo "SSL check failed, attempting HTTP..."
    curl -fsSL "http://$HOST/bin/$BINARY" -o "$TEMP_DIR/ciotx"
fi

# Make executable and move to PATH
chmod +x "$TEMP_DIR/ciotx"

echo "${BLUE}Installing to /usr/local/bin (requires sudo)...${NC}"
if [ -w /usr/local/bin ]; then
    mv "$TEMP_DIR/ciotx" /usr/local/bin/ciotx
else
    sudo mv "$TEMP_DIR/ciotx" /usr/local/bin/ciotx
fi

rm -rf "$TEMP_DIR"

echo "${GREEN}✓ CIOTX CLI installed successfully!${NC}"
echo "Run ${BLUE}ciotx login${NC} to authenticate."
