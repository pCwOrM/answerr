#!/usr/bin/env python3
"""
Generates and validates sitemap.xml for answerr.me.
Ensures that all canonical public pages are indexed with valid lastmod,
appropriate changefreq and priority, and that no noindex pages are submitted
to Google Search Console.

Usage:
    python scripts/build_sitemap.py           # writes sitemap.xml
    python scripts/build_sitemap.py --check   # exits 1 if sitemap.xml is out of date (CI)
"""

from datetime import datetime
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITEMAP_FILE = os.path.join(ROOT, "sitemap.xml")

ENTRIES = [
    # (canonical_url, rel_path, changefreq, priority)
    ("https://answerr.me/", "index.html", "daily", "1.0"),
    ("https://answerr.me/pro/docs.html", "pro/docs.html", "weekly", "0.9"),
    ("https://answerr.me/pro/pricing.html", "pro/pricing.html", "weekly", "0.9"),
    ("https://answerr.me/pro/studio.html", "pro/studio.html", "weekly", "0.8"),
    ("https://answerr.me/pro/research.html", "pro/research.html", "weekly", "0.8"),
    ("https://answerr.me/chat.html", "chat.html", "weekly", "0.7"),
    ("https://answerr.me/pro/status.html", "pro/status.html", "weekly", "0.6"),
    ("https://answerr.me/pro/legal/kullanim-sartlari.html", "pro/legal/kullanim-sartlari.html", "monthly", "0.4"),
    ("https://answerr.me/pro/legal/gizlilik.html", "pro/legal/gizlilik.html", "monthly", "0.4"),
    ("https://answerr.me/pro/legal/kvkk-aydinlatma.html", "pro/legal/kvkk-aydinlatma.html", "monthly", "0.4"),
    ("https://answerr.me/pro/legal/cerez.html", "pro/legal/cerez.html", "monthly", "0.4"),
    ("https://answerr.me/pro/legal/mesafeli-satis.html", "pro/legal/mesafeli-satis.html", "monthly", "0.4"),
    ("https://answerr.me/pro/legal/on-bilgilendirme.html", "pro/legal/on-bilgilendirme.html", "monthly", "0.4"),
    ("https://answerr.me/pro/legal/iade-iptal.html", "pro/legal/iade-iptal.html", "monthly", "0.4"),
    ("https://answerr.me/pro/legal/veri-isleme.html", "pro/legal/veri-isleme.html", "monthly", "0.4"),
]


def get_lastmod(rel_path: str) -> str:
    full_path = os.path.join(ROOT, rel_path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Page file not found: {rel_path}")

    # Try getting the last git commit date for this path
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", rel_path],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        date_str = r.stdout.strip()
        if date_str and re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            return date_str
    except Exception:
        pass

    # Fallback to local modification date
    mtime = os.path.getmtime(full_path)
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")


def validate_page(url: str, rel_path: str) -> None:
    full_path = os.path.join(ROOT, rel_path)
    with open(full_path, encoding="utf-8") as f:
        content = f.read()

    # Google Search Console error prevention: never submit noindex pages
    if re.search(r'<meta\s+name=["\']robots["\']\s+content=["\'][^"\']*noindex', content, re.I):
        raise ValueError(f"CRITICAL: {rel_path} has a 'noindex' meta tag and MUST NOT be in sitemap.xml!")

    # Verify canonical matches the sitemap url
    canonical_match = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', content, re.I)
    if not canonical_match:
        raise ValueError(f"Page {rel_path} is missing a canonical link!")
    canonical = canonical_match.group(1)
    if canonical != url:
        raise ValueError(f"Canonical mismatch in {rel_path}: expected {url}, got {canonical}")


def generate_sitemap_xml() -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    for url, rel_path, changefreq, priority in ENTRIES:
        validate_page(url, rel_path)
        lastmod = get_lastmod(rel_path)
        lines.append("  <url>")
        lines.append(f"    <loc>{url}</loc>")
        lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append(f"    <changefreq>{changefreq}</changefreq>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append("  </url>")

    lines.append("</urlset>\n")
    return "\n".join(lines)


def main() -> int:
    check_mode = "--check" in sys.argv
    new_xml = generate_sitemap_xml()

    if check_mode:
        if not os.path.exists(SITEMAP_FILE):
            print("sitemap.xml does not exist!", file=sys.stderr)
            return 1
        with open(SITEMAP_FILE, encoding="utf-8") as f:
            existing = f.read()
        if existing != new_xml:
            print("sitemap.xml is out of date! Run: python scripts/build_sitemap.py", file=sys.stderr)
            return 1
        print("sitemap.xml is up to date.")
        return 0

    with open(SITEMAP_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_xml)
    print(f"Generated {SITEMAP_FILE} with {len(ENTRIES)} canonical URLs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
