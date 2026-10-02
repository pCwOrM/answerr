/**
 * docs.js - Controller for answerr API Documentation (answerr.me/docs.html)
 * Provides active scroll spy, code copy buttons, and bilingual TR/EN support.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Theme Persistence & Toggle
  const savedTheme = localStorage.getItem('answerr-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  const btnDocsTheme = document.getElementById('btn-docs-theme');
  if (btnDocsTheme) {
    btnDocsTheme.innerHTML = savedTheme === 'dark' ? '🌙' : '☀️';
    btnDocsTheme.addEventListener('click', () => {
      const curTheme = document.documentElement.getAttribute('data-theme') || 'dark';
      const nextTheme = curTheme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', nextTheme);
      localStorage.setItem('answerr-theme', nextTheme);
      btnDocsTheme.innerHTML = nextTheme === 'dark' ? '🌙' : '☀️';
    });
  }

  // 1. Copy Code snippet to clipboard
  const copyButtons = document.querySelectorAll('.btn-copy-code');
  copyButtons.forEach(btn => {
    btn.addEventListener('click', async () => {
      const targetId = btn.getAttribute('data-target');
      const codeEl = document.getElementById(targetId);
      if (!codeEl) return;

      try {
        await navigator.clipboard.writeText(codeEl.innerText.trim());
        const originalText = btn.innerText;
        btn.innerText = 'Kopyalandı! ✓';
        btn.style.borderColor = 'var(--emerald)';
        btn.style.color = 'var(--emerald)';

        setTimeout(() => {
          btn.innerText = originalText;
          btn.style.borderColor = '';
          btn.style.color = '';
        }, 2000);
      } catch (err) {
        console.error('Copy failed:', err);
      }
    });
  });

  // 2. Scroll Spy for Sidebar Active Links
  const sections = document.querySelectorAll('.docs-section');
  const navLinks = document.querySelectorAll('.docs-nav-item');

  function updateActiveNav() {
    let currentId = '';
    const scrollPos = window.scrollY + 120;

    sections.forEach(sec => {
      const top = sec.offsetTop;
      const height = sec.offsetHeight;
      if (scrollPos >= top && scrollPos < top + height) {
        currentId = sec.getAttribute('id');
      }
    });

    if (currentId) {
      navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${currentId}`) {
          link.classList.add('active');
        }
      });
    }
  }

  window.addEventListener('scroll', updateActiveNav);
  updateActiveNav();

  // 3. Language Switcher (TR / EN)
  let currentLang = localStorage.getItem('answerr_lang') || 'tr';
  const langBtn = document.getElementById('btn-docs-lang');
  const langText = document.getElementById('docs-lang-text');

  function updateDocsLang(lang) {
    currentLang = lang;
    localStorage.setItem('answerr_lang', lang);
    if (langText) langText.innerText = lang.toUpperCase();
    document.documentElement.lang = lang;
  }

  if (langBtn) {
    langBtn.addEventListener('click', () => {
      const nextLang = currentLang === 'tr' ? 'en' : 'tr';
      updateDocsLang(nextLang);
    });
  }

  updateDocsLang(currentLang);

  // Mobile Navigation Drawer Toggle & Backdrop
  const btnMobileMenu = document.getElementById('btn-mobile-menu');
  const btnCloseDrawer = document.getElementById('btn-close-drawer');
  const mobileNavDrawer = document.getElementById('mobile-nav-drawer');
  const mobileDrawerBackdrop = document.getElementById('mobile-drawer-backdrop');

  function openMobileDrawer() {
    if (mobileNavDrawer) mobileNavDrawer.classList.add('open');
    if (mobileDrawerBackdrop) mobileDrawerBackdrop.classList.add('open');
    if (btnMobileMenu) {
      btnMobileMenu.classList.add('open');
      btnMobileMenu.setAttribute('aria-expanded', 'true');
    }
    document.body.style.overflow = 'hidden';
  }

  function closeMobileDrawer() {
    if (mobileNavDrawer) mobileNavDrawer.classList.remove('open');
    if (mobileDrawerBackdrop) mobileDrawerBackdrop.classList.remove('open');
    if (btnMobileMenu) {
      btnMobileMenu.classList.remove('open');
      btnMobileMenu.setAttribute('aria-expanded', 'false');
    }
    document.body.style.overflow = '';
  }

  if (btnMobileMenu) {
    btnMobileMenu.addEventListener('click', (e) => {
      e.stopPropagation();
      if (mobileNavDrawer && mobileNavDrawer.classList.contains('open')) {
        closeMobileDrawer();
      } else {
        openMobileDrawer();
      }
    });
  }
  if (btnCloseDrawer) btnCloseDrawer.addEventListener('click', closeMobileDrawer);
  if (mobileDrawerBackdrop) mobileDrawerBackdrop.addEventListener('click', closeMobileDrawer);

  document.querySelectorAll('[data-nav-close]').forEach(link => {
    link.addEventListener('click', closeMobileDrawer);
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeMobileDrawer();
    }
  });
});
