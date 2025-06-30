#!/bin/bash
# Setup a launch agent to run the email categorizer on startup

# Get the current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Create the launch agent plist file
PLIST_FILE="$HOME/Library/LaunchAgents/com.sunlec.emailcategorizer.plist"

echo "Creating launch agent..."
cat > "$PLIST_FILE" << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.sunlec.emailcategorizer</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>${SCRIPT_DIR}/email_categorizer_continuous.py</string>
        <string>300</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${SCRIPT_DIR}/categorizer.log</string>
    <key>StandardErrorPath</key>
    <string>${SCRIPT_DIR}/categorizer_error.log</string>
    <key>WorkingDirectory</key>
    <string>${SCRIPT_DIR}</string>
</dict>
</plist>
EOL

# Set permissions
chmod 644 "$PLIST_FILE"

echo "Launch agent created at $PLIST_FILE"
echo "To load the launch agent now, run:"
echo "launchctl load $PLIST_FILE"
echo ""
echo "To unload it later if needed, run:"
echo "launchctl unload $PLIST_FILE"
