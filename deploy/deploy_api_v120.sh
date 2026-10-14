#!/usr/bin/env bash
# answerr API 1.2.0 — server deployment with automatic rollback.
# Run as root on the API host from the unpacked bundle directory:
#   sudo bash deploy/deploy_api_v120.sh
# Touches only: the answerr-api service, its app directory, /etc/answerr, /var/lib/answerr
# and (if needed) one proxy header line in the api.answerr.me nginx site.
set -euo pipefail

SRC="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE=answerr-api
TS="$(date +%Y%m%d_%H%M%S)"
BK="/opt/backups/answerr_api_v120_${TS}"
log() { printf '[deploy %s] %s\n' "$(date +%H:%M:%S)" "$*"; }
die() { log "ERROR: $*"; exit 1; }

[ "$(id -u)" = 0 ] || die "run as root"
systemctl cat "$SERVICE" >/dev/null 2>&1 || die "service $SERVICE not found"

EXEC="$(systemctl show -p ExecStart --value "$SERVICE" | sed -n 's/.*argv\[\]=\([^;]*\);.*/\1/p' | head -1)"
[ -n "$EXEC" ] || EXEC="$(systemctl cat "$SERVICE" | sed -n 's/^ExecStart=//p' | tail -1)"
APP="$(systemctl show -p WorkingDirectory --value "$SERVICE")"
OWNER="$(systemctl show -p User --value "$SERVICE")"; OWNER="${OWNER:-root}"
GROUP="$(systemctl show -p Group --value "$SERVICE")"; GROUP="${GROUP:-$OWNER}"
MOD="$(printf '%s' "$EXEC" | grep -o '[A-Za-z_][A-Za-z0-9_]*:app' | head -1 | cut -d: -f1)"; MOD="${MOD:-server}"
UVI="$(printf '%s' "$EXEC" | awk '{print $1}')"
PY="$(dirname "$UVI")/python"
PORT="$(printf '%s' "$EXEC" | grep -o -- '--port [0-9]*' | awk '{print $2}')"; PORT="${PORT:-8560}"
log "service=$SERVICE app=$APP module=$MOD user=$OWNER python=$PY port=$PORT"
[ -d "$APP" ] && [ -x "$PY" ] || die "app dir or python not found"

# 1. backup
mkdir -p "$BK"
cp -a "$APP" "$BK/app"
systemctl cat "$SERVICE" > "$BK/unit.txt"
[ -d "/etc/systemd/system/${SERVICE}.service.d" ] && cp -a "/etc/systemd/system/${SERVICE}.service.d" "$BK/dropins"
[ -f /etc/answerr/answerr.env ] && cp -a /etc/answerr/answerr.env "$BK/answerr.env"
cat > "$BK/RESTORE.txt" <<EOF
rm -f /etc/systemd/system/${SERVICE}.service.d/answerr-v120.conf
rsync -a --delete "$BK/app/" "$APP/"
systemctl daemon-reload && systemctl restart $SERVICE
EOF
log "backup: $BK"

rollback() {
  log "ROLLBACK"
  rm -f "/etc/systemd/system/${SERVICE}.service.d/answerr-v120.conf"
  rsync -a --delete "$BK/app/" "$APP/"
  systemctl daemon-reload
  systemctl restart "$SERVICE" || true
  die "deployment rolled back; backup kept at $BK"
}

# 2. werr research engine must be importable inside the sandbox (ProtectHome=true hides /home)
WERR_PATH=""
if ! sudo -u "$OWNER" "$PY" -c "import werr" >/dev/null 2>&1; then
  for c in /opt/apps/answerr/werr /opt/apps/werr /home/pcworm/werr; do
    if [ -d "$c/werr" ]; then WERR_PATH="$c"; break; fi
  done
  [ -n "$WERR_PATH" ] || die "werr package not importable and not found"
  case "$WERR_PATH" in
    /home/*)
      mkdir -p /opt/apps/answerr/werr_pkg
      rsync -a --delete "$WERR_PATH/werr/" /opt/apps/answerr/werr_pkg/werr/
      chown -R "$OWNER:$GROUP" /opt/apps/answerr/werr_pkg
      WERR_PATH=/opt/apps/answerr/werr_pkg
      log "copied werr out of /home to $WERR_PATH (sandbox cannot read /home)";;
  esac
fi

# 3. environment file (created once; never overwritten)
mkdir -p /etc/answerr
if [ ! -f /etc/answerr/answerr.env ]; then
  KEY="$(openssl rand -hex 24)"
  cat > /etc/answerr/answerr.env <<EOF
# answerr API 1.2.0 — created $TS
# tenant:key pairs, comma separated (keys >= 24 chars)
ANSWERR_API_KEYS=itouch:${KEY}
ANSWERR_GATES_PATH=/var/lib/answerr/gates.json
ANSWERR_TRUSTED_PROXIES=127.0.0.1,::1
# reCAPTCHA v3 secret for site key 6LdP-JgqAAAAAJLdy_W8uowqstSa4XKlJTOkVAux (registered for answerr.me)
RECAPTCHA_SECRET=
RECAPTCHA_MIN_SCORE=0.5
RECAPTCHA_HOSTNAMES=answerr.me,www.answerr.me
ANSWERR_WERR_PATH=${WERR_PATH}
EOF
  log "created /etc/answerr/answerr.env with a new API key for tenant 'itouch'"
elif [ -n "$WERR_PATH" ] && ! grep -q '^ANSWERR_WERR_PATH=' /etc/answerr/answerr.env; then
  echo "ANSWERR_WERR_PATH=${WERR_PATH}" >> /etc/answerr/answerr.env
fi
chown root:"$GROUP" /etc/answerr/answerr.env
chmod 640 /etc/answerr/answerr.env

# 4. install code
install -o "$OWNER" -g "$GROUP" -m 0640 "$SRC/api_server.py" "$APP/${MOD}.py"
install -o "$OWNER" -g "$GROUP" -m 0640 "$SRC/api_server.py" "$APP/api_server.py"
for f in policy_kernel.py policy_checks.py policy_compiler.py; do
  install -o "$OWNER" -g "$GROUP" -m 0640 "$SRC/$f" "$APP/$f"
done
install -d -o "$OWNER" -g "$GROUP" -m 0750 "$APP/policies"
install -o "$OWNER" -g "$GROUP" -m 0640 "$SRC/policies/builtin_gates.json" "$APP/policies/builtin_gates.json"

# 5. systemd drop-in: env file, state dir, our own client-IP logic (no uvicorn proxy rewrite)
NEWEXEC="$EXEC"
printf '%s' "$NEWEXEC" | grep -q -- '--no-proxy-headers' || NEWEXEC="$NEWEXEC --no-proxy-headers"
mkdir -p "/etc/systemd/system/${SERVICE}.service.d"
cat > "/etc/systemd/system/${SERVICE}.service.d/answerr-v120.conf" <<EOF
[Service]
EnvironmentFile=-/etc/answerr/answerr.env
StateDirectory=answerr
StateDirectoryMode=0750
ReadWritePaths=/var/lib/answerr
ExecStart=
ExecStart=$NEWEXEC
EOF

# 6. import test as the service user, with the real environment, before restarting
set -a; . /etc/answerr/answerr.env; set +a
export ANSWERR_GATES_PATH="/tmp/answerr_deploy_test_${TS}.json"
if ! sudo -u "$OWNER" --preserve-env=ANSWERR_API_KEYS,ANSWERR_GATES_PATH,ANSWERR_WERR_PATH,RECAPTCHA_SECRET \
     bash -c "cd '$APP' && '$PY' -c 'import ${MOD} as m; print(\"import ok\", m.API_VERSION)'"; then
  rollback
fi
rm -f "$ANSWERR_GATES_PATH" "$ANSWERR_GATES_PATH.lock"

# 7. restart and verify
systemctl daemon-reload
systemctl restart "$SERVICE"
ok=0
for i in $(seq 1 20); do
  sleep 1
  if curl -fsS "http://127.0.0.1:${PORT}/v1/health" 2>/dev/null | grep -q '"api_version":"1.2.0"'; then ok=1; break; fi
done
[ "$ok" = 1 ] || rollback
V="$(curl -fsS -X POST "http://127.0.0.1:${PORT}/v1/decide" -H 'Content-Type: application/json' \
  -d '{"gate_id":"agent_mcp_guard","strict_policy":true,"state":{"tool_name":"bulk_delete_users","user_role":"admin","auth_status":true},"questions":{"q":{"type":"noul","text":"Allow?"}}}' \
  | "$PY" -c 'import sys,json;print(json.load(sys.stdin)["verdict"])')" || rollback
[ "$V" = "DENY" ] || { log "functional check returned $V"; rollback; }
log "health and functional check passed (bulk_delete_users -> DENY)"

# 8. nginx: make sure the API site passes the real client address
NGX="$(grep -rl 'api.answerr.me' /etc/nginx/sites-enabled/ 2>/dev/null | head -1 || true)"
if [ -n "$NGX" ]; then
  NGX="$(readlink -f "$NGX")"
  if ! grep -q 'X-Real-IP' "$NGX"; then
    cp -a "$NGX" "$BK/nginx_site.conf"
    sed -i 's/^\(\s*\)proxy_pass\(.*\)$/\1proxy_pass\2\n\1proxy_set_header X-Real-IP $remote_addr;/' "$NGX"
    if nginx -t 2>/dev/null; then systemctl reload nginx; log "nginx: added X-Real-IP to $NGX"
    else cp -a "$BK/nginx_site.conf" "$NGX"; log "nginx test failed; left the site unchanged"; fi
  else
    log "nginx: X-Real-IP already set in $NGX"
  fi
else
  log "nginx: no site for api.answerr.me found under sites-enabled; check proxy headers manually"
fi

# 9. code version record
if [ -d /data/answerr_code_versions ]; then
  mkdir -p "/data/answerr_code_versions/${TS}_v120"
  cp -a "$APP"/*.py "$APP/policies" "/data/answerr_code_versions/${TS}_v120/" 2>/dev/null || true
fi

log "done. API key(s): /etc/answerr/answerr.env (root:$GROUP 640)."
grep -q '^RECAPTCHA_SECRET=$' /etc/answerr/answerr.env && log "reCAPTCHA secret is empty: browser requests run at the anonymous rate tier until it is set."
log "restore instructions: $BK/RESTORE.txt"
