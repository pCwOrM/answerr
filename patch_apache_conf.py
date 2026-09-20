#!/usr/bin/env python3
import re
import sys

CONF_PATH = '/etc/apache2/sites-available/mechsrv-ssl.conf'

with open(CONF_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update ServerAlias
if 'api.answerr.me' not in content:
    content = re.sub(
        r'(ServerAlias\s+mechsrv\.itouch\.fi\s+www\.mechsrv\.itouch\.fi)',
        r'\1 api.answerr.me',
        content,
        count=1
    )

# 2. Add Answerr API Proxy Block if not already present
if 'ANSWERR REFLEX DECISION ENGINE REST API' not in content:
    proxy_block = '''
    # --- ANSWERR REFLEX DECISION ENGINE REST API (PORT 8560) ---
    <Location /v1>
        LimitRequestBody 65536
        Header always set Access-Control-Allow-Origin "*"
        Header always set Access-Control-Allow-Methods "GET, POST, OPTIONS"
        Header always set Access-Control-Allow-Headers "Content-Type, Authorization, X-Client-Version"
    </Location>
    ProxyPass /v1 http://127.0.0.1:8560/v1
    ProxyPassReverse /v1 http://127.0.0.1:8560/v1

    <Location /answerr>
        LimitRequestBody 65536
        Header always set Access-Control-Allow-Origin "*"
        Header always set Access-Control-Allow-Methods "GET, POST, OPTIONS"
        Header always set Access-Control-Allow-Headers "Content-Type, Authorization, X-Client-Version"
    </Location>
    ProxyPass /answerr/ http://127.0.0.1:8560/
    ProxyPassReverse /answerr/ http://127.0.0.1:8560/
'''
    # Insert before the closing </VirtualHost>
    idx = content.rfind('</VirtualHost>')
    if idx != -1:
        content = content[:idx] + proxy_block + '\n' + content[idx:]
    else:
        print("ERROR: </VirtualHost> tag not found!")
        sys.exit(1)

with open(CONF_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] mechsrv-ssl.conf patched successfully!")
