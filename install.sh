#!/data/data/com.termux/files/usr/bin/bash
# Installer for Password Auditor Tool
# Created by Sreerag

TOOL_NAME="SPA"
INSTALL_DIR="/data/data/com.termux/files/usr/bin"
SOURCE_FILE="$HOME/github_project/pwauditor.py"
TARGET_FILE="$INSTALL_DIR/$TOOL_NAME"

echo "🔐 Installing $TOOL_NAME ..."

# Check if source exists
if [ ! -f "$SOURCE_FILE" ]; then
    echo "❌ $SOURCE_FILE not found!"
    exit 1
fi

# Copy to bin
cp "$SOURCE_FILE" "$TARGET_FILE"

# Add shebang if missing
if ! head -n1 "$TARGET_FILE" | grep -q "python"; then
    sed -i '1i #!/usr/bin/env python3' "$TARGET_FILE"
fi

# Make executable
chmod +x "$TARGET_FILE"

echo "✅ Installed successfully!"
echo "👉 You can now run the tool using: $TOOL_NAME"
