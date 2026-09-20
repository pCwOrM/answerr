#!/usr/bin/env python3
import re
import sys

CONF_PATH = '/etc/apache2/sites-available/mechsrv-ssl.conf'

with open(CONF_PATH, 'r', encoding='latin-1') as f:
    content = f.read()

# 1. Update ServerAlias if needed
if 'api.answerr.me' not in content:
    content = re.sub(
        r'(ServerAlias\s+mechsrv\.itouch\.fi\s+www\.mechsrv\.itouch\.fi)',
        r'\1 api.answerr.me',
        content,
        count=1
    )

# 2. Update existing Answerr block with security enhancements if present
if '# --- ANSWERR REFLEX DECISION ENGINE REST API (PORT 8560) ---' in content:
    # Add ProxyPreserveHost and ProxyTimeout if not already added
    if 'ProxyPreserveHost On' not in content:
        content = content.replace(
            '# --- ANSWERR REFLEX DECISION ENGINE REST API (PORT 8560) ---',
            '# --- ANSWERR REFLEX DECISION ENGINE REST API (PORT 8560) ---\n    ProxyPreserveHost On\n    ProxyTimeout 15'
        )

    # Add security headers to Location blocks
    if 'Referrer-Policy' not in content:
        content = content.replace(
            'Header always set Access-Control-Allow-Headers "Content-Type, Authorization, X-Client-Version"',
            'Header always set Access-Control-Allow-Headers "Content-Type, Authorization, X-Client-Version"\n        Header always set X-Content-Type-Options "nosniff"\n        Header always set X-Frame-Options "SAMEORIGIN"\n        Header always set Referrer-Policy "strict-origin-when-cross-origin"'
        )
else:
    # Fresh block insertion
    proxy_block = '''
    # --- ANSWERR REFLEX DECISION ENGINE REST API (PORT 8560) ---
    ProxyPreserveHost On
    ProxyTimeout 15

    <Location /v1>
        LimitRequestBody 65536
        Header always set Access-Control-Allow-Origin "*"
        Header always set Access-Control-Allow-Methods "GET, POST, OPTIONS"
        Header always set Access-Control-Allow-Headers "Content-Type, Authorization, X-Client-Version"
        Header always set X-Content-Type-Options "nosniff"
        Header always set X-Frame-Options "SAMEORIGIN"
        Header always set Referrer-Policy "strict-origin-when-cross-origin"
    </Location>
    ProxyPass /v1 http://127.0.0.1:8560/v1 timeout=15 retry=0
    ProxyPassReverse /v1 http://127.0.0.1:8560/v1

    <Location /answerr>
        LimitRequestBody 65536
        Header always set Access-Control-Allow-Origin "*"
        Header always set Access-Control-Allow-Methods "GET, POST, OPTIONS"
        Header always set Access-Control-Allow-Headers "Content-Type, Authorization, X-Client-Version"
        Header always set X-Content-Type-Options "nosniff"
        Header always set X-Frame-Options "SAMEORIGIN"
        Header always set Referrer-Policy "strict-origin-when-cross-origin"
    </Location>
    ProxyPass /answerr/ http://127.0.0.1:8560/ timeout=15 retry=0
    ProxyPassReverse /answerr/ http://127.0.0.1:8560/
'''
    idx = content.rfind('</VirtualHost>')
    if idx != -1:
        content = content[:idx] + proxy_block + '\n' + content[idx:]
    else:
        print("ERROR: </VirtualHost> tag not found!")
        sys.exit(1)

with open(CONF_PATH, 'w', encoding='latin-1') as f:
    f.write(content)

print("[OK] mechsrv-ssl.conf patched with Apache security headers & timeouts successfully!")
