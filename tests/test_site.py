"""Static site invariants: one navigation for every /pro page, legal pages present, docs links point to /v1/docs."""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRO = os.path.join(ROOT, "pro")
PAGES = ["index.html", "studio.html", "research.html", "pricing.html", "vision.html", "docs.html", "status.html",
         "console/index.html", "console/admin.html"]


def nav_of(rel):
    s = open(os.path.join(PRO, rel), encoding="utf-8").read()
    m = re.search(r"CHROME:NAV:START.*?CHROME:NAV:END", s, re.S)
    assert m, rel
    n = re.sub(r' aria-current="page"', "", m.group(0))
    return n.replace('href="../', 'href="')


def test_chrome_is_up_to_date():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "build_site_chrome.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_every_page_has_the_same_menu():
    navs = {rel: nav_of(rel) for rel in PAGES}
    first = navs["index.html"]
    for rel, n in navs.items():
        assert n == first, rel


def test_legal_pages_exist_and_footer_links_resolve():
    for slug in ("kullanim-sartlari", "kvkk-aydinlatma", "gizlilik", "on-bilgilendirme", "mesafeli-satis", "iade-iptal", "cerez", "veri-isleme"):
        assert os.path.exists(os.path.join(PRO, "legal", slug + ".html")), slug
    s = open(os.path.join(PRO, "index.html"), encoding="utf-8").read()
    for href in re.findall(r'href="([^"#:]+\.html)"', s):
        assert os.path.exists(os.path.normpath(os.path.join(PRO, href))), href


def test_no_page_links_the_dead_docs_url():
    for rel in PAGES:
        s = open(os.path.join(PRO, rel), encoding="utf-8").read()
        assert "api.answerr.me/docs" not in s, rel


def test_root_index_promoted_and_archives_kept_off_pages():
    root_idx = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    assert 'href="pro/pro.css' in root_idx
    assert 'src="pro/console.js' in root_idx
    assert 'id="werrPresetSel"' in root_idx
    for href in re.findall(r'href="([^"#:]+\.html)"', root_idx):
        assert os.path.exists(os.path.normpath(os.path.join(ROOT, href))), href
    # Old versions are removed from the public web tree
    assert not os.path.exists(os.path.join(PRO, "archive")), "pro/archive must not exist in web root"
    assert not os.path.exists(os.path.join(ROOT, "research")), "research folder must not exist in web root"
    # Old versions are safely preserved in repo archive/site/
    assert os.path.exists(os.path.join(ROOT, "archive", "site", "2026-10-15-root-v4.1", "index.html"))
    assert os.path.exists(os.path.join(ROOT, "archive", "site", "2026-10-14-v1.2", "index.html"))
    assert os.path.exists(os.path.join(ROOT, "archive", "site", "2026-10-13-v0.6", "index.html"))
    assert os.path.exists(os.path.join(ROOT, "archive", "site", "research-portal", "portal.html"))
    assert os.path.exists(os.path.join(ROOT, "archive", "site", "docs-v1.0.html"))
