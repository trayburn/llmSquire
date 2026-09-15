#!/bin/bash
# setup-api-key.sh — Configure Ollama Cloud API key for llmSquire
#
# This script:
#   1. Prompts for your Ollama Cloud API key (input is hidden)
#   2. Writes a .env file with the Ollama Cloud configuration
#   3. Sets the GitHub secret LLMSQUIRE_API_KEY on the trayburn/llmSquire repo
#
# Usage: bash setup-api-key.sh

set -euo pipefail

REPO="trayburn/llmSquire"
ENV_FILE="$(dirname "$0")/.env"

echo "=== llmSquire API Key Setup (Ollama Cloud) ==="
echo
echo "You need an Ollama Cloud API key."
echo "Get one at: https://ollama.com/settings/api-keys"
echo

# Prompt for the key (hidden input)
read -s -p "Enter your Ollama Cloud API key: " API_KEY
echo
echo

if [ -z "$API_KEY" ]; then
    echo "ERROR: No API key entered. Aborting."
    exit 1
fi

# --- 1. Write .env file ---
echo "Writing .env file..."
cat > "$ENV_FILE" << EOF
# llmSquire — LLM API Configuration (Ollama Cloud)
LLMSQUIRE_API_BASE=https://ollama.com/v1
LLMSQUIRE_MODEL=deepseek-v4-flash:cloud
LLMSQUIRE_API_KEY=$API_KEY
EOF
chmod 600 "$ENV_FILE"
echo "  Created: $ENV_FILE"
echo

# --- 2. Set GitHub secret ---
echo "Setting GitHub secret on $REPO..."
if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
    echo "$API_KEY" | gh secret set LLMSQUIRE_API_KEY --repo "$REPO"
    echo "  Secret 'LLMSQUIRE_API_KEY' set on $REPO"
else
    echo "  WARNING: gh CLI not available or not authenticated."
    echo "  To set the secret manually:"
    echo "    echo '$API_KEY' | gh secret set LLMSQUIRE_API_KEY --repo $REPO"
fi
echo

# --- 3. Verify ---
echo "=== Verification ==="
if [ -f "$ENV_FILE" ]; then
    echo "  .env file: OK"
    # Verify the key is in the file (without printing it)
    if grep -q "LLMSQUIRE_API_KEY=" "$ENV_FILE"; then
        echo "  API key in .env: OK"
    fi
else
    echo "  .env file: MISSING"
fi

if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
    SECRETS=$(gh secret list --repo "$REPO" 2>/dev/null || true)
    if echo "$SECRETS" | grep -q "LLMSQUIRE_API_KEY"; then
        echo "  GitHub secret: OK"
    else
        echo "  GitHub secret: NOT FOUND (may take a moment to propagate)"
    fi
fi
echo
echo "=== Done ==="
echo
echo "You can now run the koans locally:"
echo "  cd $(dirname "$0")"
echo "  python3 -m llmsquire"
echo
echo "Or run the test suite:"
echo "  python3 -m pytest tests/ -v"