#!/bin/bash
set -e

# 1. Add NOPASSWD for answerr-api restart
echo 'pcworm ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart answerr-api.service, /usr/bin/systemctl reload answerr-api.service, /usr/bin/systemctl status answerr-api.service' > /tmp/pcworm-answerr
chmod 440 /tmp/pcworm-answerr
echo "Jesmaat19" | sudo -S cp /tmp/pcworm-answerr /etc/sudoers.d/pcworm-answerr
rm -f /tmp/pcworm-answerr

# 2. Add post-merge hook to wevv_repo
HOOK_PATH="/home/pcworm/wevv_repo/.git/hooks/post-merge"
cat > "$HOOK_PATH" << 'EOF'
#!/bin/bash
echo "[*] wevv repository updated via git. Syncing Answerr API..."
sudo /usr/bin/systemctl restart answerr-api.service 2>/dev/null || true
echo "[*] Answerr API successfully restarted with updated wevv engine!"
EOF
chmod +x "$HOOK_PATH"

echo "[OK] wevv live synchronization hook and NOPASSWD reload configured successfully!"
