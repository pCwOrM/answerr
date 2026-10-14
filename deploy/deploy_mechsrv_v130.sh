#!/usr/bin/env bash
# answerr API 1.3.0 (commercial layer) on mechsrv — canary first, then swap, with automatic rollback.
#   sudo bash deploy/deploy_mechsrv_v130.sh            # full run
#   sudo bash deploy/deploy_mechsrv_v130.sh --rollback  # restore the latest v130 backup (API code; the commerce DB is kept)
# Chain: IIS/Plesk (api.answerr.me:443) -> VirtualBox NAT -> Apache :4431 (/v1 -> 127.0.0.1:8560) -> uvicorn
set -euo pipefail

SRC="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE=answerr-api
APP=/opt/apps/answerr/api
VENV=/opt/apps/answerr/venv
PY="$VENV/bin/python"
OWNER=pcworm
PORT=8560
CANARY_PORT=8561
ENVF=/etc/answerr/answerr.env
DROPIN_DIR=/etc/systemd/system/${SERVICE}.service.d
DROPIN=$DROPIN_DIR/answerr-v120.conf
TS="$(date +%Y%m%d_%H%M%S)"
BK_ROOT=/opt/backups
VER=1.3.0
BK="$BK_ROOT/answerr_api_v130_${TS}"
log() { printf '[deploy %s] %s\n' "$(date +%H:%M:%S)" "$*"; }
die() { log "ERROR: $*"; exit 1; }
[ "$(id -u)" = 0 ] || die "run as root"

restore_from() {
  local b="$1"
  log "ROLLBACK from $b"
  systemctl stop answerr-canary 2>/dev/null || true
  rm -f "$DROPIN"
  [ -f "$b/answerr-v120.conf.prev" ] && cp -a "$b/answerr-v120.conf.prev" "$DROPIN"
  rsync -a --delete "$b/api/" "$APP/"
  systemctl daemon-reload
  systemctl restart "$SERVICE"
  sleep 4
  curl -fsS "http://127.0.0.1:$PORT/v1/health" >/dev/null && log "previous version is serving again" || log "WARNING: health check after rollback failed"
}

if [ "${1:-}" = "--rollback" ]; then
  last="$(ls -1d $BK_ROOT/answerr_api_v130_* 2>/dev/null | tail -1)"
  [ -n "$last" ] || die "no backup found"
  restore_from "$last"; exit 0
fi

# ---------------------------------------------------------------- 0. preflight
systemctl is-active --quiet "$SERVICE" || die "$SERVICE is not running; refusing to deploy on a broken base"
[ -x "$PY" ] || die "venv python missing"
sudo -u "$OWNER" "$PY" -c "import werr, fastapi, uvicorn, pydantic" || die "venv lacks runtime packages"
for f in api_server.py policy_kernel.py policy_checks.py policy_compiler.py access_mailer.py policies/builtin_gates.json commerce/store.py commerce/router.py commerce/plans.json; do
  [ -f "$SRC/$f" ] || die "bundle incomplete: $f"
done

# ---------------------------------------------------------------- 1. backup
mkdir -p "$BK"
cp -a "$APP" "$BK/api"
systemctl cat "$SERVICE" > "$BK/unit.txt"
[ -f "$DROPIN" ] && cp -a "$DROPIN" "$BK/answerr-v120.conf.prev"
[ -f "$ENVF" ] && cp -a "$ENVF" "$BK/answerr.env.prev"
cat > "$BK/RESTORE.txt" <<EOF
sudo bash $SRC/deploy/deploy_mechsrv_v130.sh --rollback
# or by hand:
rm -f $DROPIN; rsync -a --delete $BK/api/ $APP/; systemctl daemon-reload; systemctl restart $SERVICE
EOF
log "backup: $BK"

# ---------------------------------------------------------------- 2. environment file (created once)
mkdir -p /etc/answerr
if [ ! -f "$ENVF" ]; then
  KEY="$(openssl rand -hex 24)"
  RSEC="$(systemctl show -p Environment --value werr-telemetry 2>/dev/null | tr ' ' '\n' | sed -n 's/^RECAPTCHA_SECRET_KEY=//p' | head -1)"
  umask 077
  cat > "$ENVF" <<EOF
# answerr API 1.2.0 — created $TS by deploy_mechsrv_v120.sh
ANSWERR_API_KEYS=itouch:${KEY}
ANSWERR_GATES_PATH=/var/lib/answerr/gates.json
ANSWERR_ACCESS_LOG=/var/lib/answerr/access_requests.jsonl
ANSWERR_TRUSTED_PROXIES=127.0.0.1,::1,10.0.2.2
RECAPTCHA_SECRET=${RSEC}
RECAPTCHA_MIN_SCORE=0.5
RECAPTCHA_HOSTNAMES=answerr.me,www.answerr.me
SMTP_HOST=mail.answerr.me
SMTP_PORT=465
SMTP_USER=ask@answerr.me
SMTP_PASSWORD=${ANSWERR_SMTP_PASSWORD:-}
MAIL_FROM_NAME="answerr · Werr Technology"
MAIL_NOTIFY_TO=ask@answerr.me
MAIL_REPLY_TO="Volkan Dagli <ask@answerr.me>, pcworm@pcworm.net"
EOF
  log "created $ENVF (new API key for tenant 'itouch'; reCAPTCHA secret $( [ -n "$RSEC" ] && echo copied from werr-telemetry || echo empty))"
fi
# 1.3.0 additions (appended once; existing values are never changed)
grep -q '^ANSWERR_ADMIN_KEY=' "$ENVF" || { echo "ANSWERR_ADMIN_KEY=adm_$(openssl rand -hex 24)" >> "$ENVF"; log "added ANSWERR_ADMIN_KEY to $ENVF"; }
grep -q '^ANSWERR_COMMERCE_DB=' "$ENVF" || echo "ANSWERR_COMMERCE_DB=/var/lib/answerr/commerce.sqlite" >> "$ENVF"
grep -q '^ANSWERR_CONSOLE_URL=' "$ENVF" || echo "ANSWERR_CONSOLE_URL=https://answerr.me/pro/console/" >> "$ENVF"
grep -q '^ANSWERR_PAYMENT_PROVIDER=' "$ENVF" || echo "ANSWERR_PAYMENT_PROVIDER=manual" >> "$ENVF"
chown root:"$OWNER" "$ENVF"; chmod 640 "$ENVF"
ADMIN_KEY="$(sed -n 's/^ANSWERR_ADMIN_KEY=//p' "$ENVF" | tail -1)"
# commerce DB snapshot (online backup; restore is manual and never automatic)
if [ -f /var/lib/answerr/commerce.sqlite ]; then
  sudo -u "$OWNER" "$PY" -c "import sqlite3,sys; s=sqlite3.connect('/var/lib/answerr/commerce.sqlite'); d=sqlite3.connect(sys.argv[1]); s.backup(d); d.close()" /tmp/answerr_commerce_$TS.sqlite \
    && mv /tmp/answerr_commerce_$TS.sqlite "$BK/commerce.sqlite" && log "commerce DB snapshot: $BK/commerce.sqlite"
fi

# ---------------------------------------------------------------- 3. stage + tests
STAGE="/opt/apps/answerr/api_v130_stage"
rm -rf "$STAGE"; mkdir -p "$STAGE"
cp -a "$SRC/api_server.py" "$SRC/policy_kernel.py" "$SRC/policy_checks.py" "$SRC/policy_compiler.py" "$SRC/access_mailer.py" "$SRC/policies" "$SRC/commerce" "$STAGE/"
find "$STAGE/commerce" -name "__pycache__" -prune -exec rm -rf {} +
mkdir -p "$STAGE/pro" && cp -a "$SRC/pro/pricing.html" "$STAGE/pro/"
cp "$SRC/api_server.py" "$STAGE/server.py"
[ -d "$SRC/tests" ] && cp -a "$SRC/tests" "$STAGE/tests"
[ -d "$SRC/js" ] && mkdir -p "$STAGE/js" && cp -a "$SRC/js/policy-kernel.js" "$STAGE/js/"
chown -R "$OWNER:$OWNER" "$STAGE"
if [ -d "$STAGE/tests" ]; then
  DEPS=/tmp/answerr_testdeps_$TS
  if sudo -u "$OWNER" "$PY" -m pip install -q --target "$DEPS" pytest httpx >/dev/null 2>&1; then
    log "running test suite in stage"
    sudo -u "$OWNER" env PYTHONPATH="$DEPS" ANSWERR_WERR_PATH=/nonexistent "$PY" -m pytest -q -p no:cacheprovider "$STAGE/tests" --ignore="$STAGE/tests/test_site.py" \
      || { rm -rf "$DEPS" "$STAGE"; die "tests failed in stage; nothing changed (backup at $BK)"; }
    rm -rf "$DEPS"
  else
    log "could not install pytest; skipping unit tests (canary checks still run)"
  fi
fi

# ---------------------------------------------------------------- 4. canary on $CANARY_PORT
mkdir -p /var/lib/answerr && chown "$OWNER:$OWNER" /var/lib/answerr && chmod 750 /var/lib/answerr
systemctl stop answerr-canary 2>/dev/null || true
systemctl reset-failed answerr-canary 2>/dev/null || true
systemd-run --unit=answerr-canary --uid="$OWNER" --gid="$OWNER" --working-directory="$STAGE" \
  -p EnvironmentFile="$ENVF" -p Environment=ANSWERR_GATES_PATH=/tmp/answerr_canary_gates.json \
  -p Environment=ANSWERR_ACCESS_LOG=/tmp/answerr_canary_access.jsonl -p Environment=SMTP_PASSWORD= \
  -p Environment=ANSWERR_RATELIMIT_DB=/tmp/answerr_canary_rl.sqlite \
  -p Environment=ANSWERR_COMMERCE_DB=/tmp/answerr_canary_commerce.sqlite \
  -p PrivateTmp=true \
  "$VENV/bin/uvicorn" server:app --host 127.0.0.1 --port "$CANARY_PORT" --workers 1 --no-proxy-headers >/dev/null
ok=0; for i in $(seq 1 20); do sleep 1; curl -fsS "http://127.0.0.1:$CANARY_PORT/v1/health" 2>/dev/null | grep -q "\"api_version\":\"$VER\"" && { ok=1; break; }; done
[ "$ok" = 1 ] || { journalctl -u answerr-canary --no-pager | tail -20; systemctl stop answerr-canary; die "canary did not start; live service untouched"; }
log "canary up on :$CANARY_PORT"
if ! ANSWERR_EXPECT_VERSION=$VER ANSWERR_ADMIN_KEY="$ADMIN_KEY" "$PY" "$SRC/deploy/smoke_checks.py" "http://127.0.0.1:$CANARY_PORT"; then
  systemctl stop answerr-canary; die "canary smoke checks failed; live service untouched"
fi
systemctl stop answerr-canary
log "canary passed"

# ---------------------------------------------------------------- 5. swap
install -o "$OWNER" -g "$OWNER" -m 0644 "$STAGE/server.py" "$APP/server.py"
for f in api_server.py policy_kernel.py policy_checks.py policy_compiler.py access_mailer.py; do
  install -o "$OWNER" -g "$OWNER" -m 0644 "$STAGE/$f" "$APP/$f"
done
install -d -o "$OWNER" -g "$OWNER" "$APP/commerce"
for f in "$STAGE"/commerce/*; do install -o "$OWNER" -g "$OWNER" -m 0644 "$f" "$APP/commerce/"; done
install -d -o "$OWNER" -g "$OWNER" "$APP/policies"
install -o "$OWNER" -g "$OWNER" -m 0644 "$STAGE/policies/builtin_gates.json" "$APP/policies/builtin_gates.json"
find "$APP/__pycache__" -name '*.pyc' -delete 2>/dev/null || true

EXEC="$(systemctl show -p ExecStart --value "$SERVICE" | sed -n 's/.*argv\[\]=\([^;]*\);.*/\1/p' | head -1 | sed 's/[[:space:]]*$//')"
printf '%s' "$EXEC" | grep -q -- '--no-proxy-headers' || EXEC="$EXEC --no-proxy-headers"
mkdir -p "$DROPIN_DIR"
cat > "$DROPIN" <<EOF
# answerr API $VER ($TS)
[Service]
EnvironmentFile=-$ENVF
StateDirectory=answerr
StateDirectoryMode=0750
ReadWritePaths=/var/lib/answerr
ExecStart=
ExecStart=$EXEC
EOF
systemctl daemon-reload
systemctl restart "$SERVICE"

ok=0; for i in $(seq 1 25); do sleep 1; curl -fsS "http://127.0.0.1:$PORT/v1/health" 2>/dev/null | grep -q "\"api_version\":\"$VER\"" && { ok=1; break; }; done
[ "$ok" = 1 ] || { journalctl -u "$SERVICE" --no-pager | tail -30; restore_from "$BK"; die "new version did not become healthy; rolled back"; }
ANSWERR_EXPECT_VERSION=$VER ANSWERR_ADMIN_KEY="$ADMIN_KEY" "$PY" "$SRC/deploy/smoke_checks.py" "http://127.0.0.1:$PORT" || { restore_from "$BK"; die "smoke checks failed on the live port; rolled back"; }

if [ -d /data/answerr_code_versions ]; then mkdir -p "/data/answerr_code_versions/${TS}_v130"; cp -a "$APP"/*.py "$APP/policies" "$APP/commerce" "/data/answerr_code_versions/${TS}_v130/"; fi
rm -rf "$STAGE"
log "DONE — answerr API $VER is live. Backup: $BK  (rollback: sudo bash $SRC/deploy/deploy_mechsrv_v130.sh --rollback)"
