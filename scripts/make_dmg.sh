#!/usr/bin/env bash
set -euo pipefail

APP_NAME="HardwareXtractor"
APP_PATH="dist/${APP_NAME}.app"
DMG_PATH="dist/${APP_NAME}.dmg"
BG_PATH="packaging/dmg_background.png"
TMP_DMG="/tmp/${APP_NAME}-tmp.dmg"
MOUNT_DIR="/Volumes/${APP_NAME}"

if [ ! -d "$APP_PATH" ]; then
  echo "ERROR: App not found at $APP_PATH" >&2
  exit 1
fi

if mount | grep -q "$MOUNT_DIR"; then
  hdiutil detach "$MOUNT_DIR" 2>/dev/null || true
fi

rm -f "$TMP_DMG" "$DMG_PATH"

hdiutil create -size 120m -fs HFS+ -volname "$APP_NAME" "$TMP_DMG" >/dev/null
hdiutil attach "$TMP_DMG" -mountpoint "$MOUNT_DIR" >/dev/null

mkdir -p "$MOUNT_DIR/.background"
cp "$BG_PATH" "$MOUNT_DIR/.background/background.png"
cp -R "$APP_PATH" "$MOUNT_DIR/"
ln -s /Applications "$MOUNT_DIR/Applications"

osascript <<EOT
  tell application "Finder"
    tell disk "${APP_NAME}"
      open
      set current view of container window to icon view
      set toolbar visible of container window to false
      set statusbar visible of container window to false
      set the bounds of container window to {200, 200, 840, 640}
      set viewOptions to the icon view options of container window
      set arrangement of viewOptions to not arranged
      set icon size of viewOptions to 96
      set background picture of viewOptions to file ".background:background.png"
      set position of item "${APP_NAME}.app" of container window to {180, 260}
      set position of item "Applications" of container window to {480, 260}
      close
      open
      update without registering applications
      delay 1
    end tell
  end tell
EOT

sync
hdiutil detach "$MOUNT_DIR" >/dev/null
hdiutil convert "$TMP_DMG" -format UDZO -o "$DMG_PATH" >/dev/null
rm -f "$TMP_DMG"

echo "Created $DMG_PATH"
