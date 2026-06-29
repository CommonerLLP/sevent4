/* theme.js — the one place that owns theme persistence and the manual toggle.
   The palette and the prefers-color-scheme default live in theme.css; this only
   handles the user's explicit, persisted override (org design rule 6).

   On change it dispatches `atlas:themechange` on document, carrying the new
   theme, so map consoles can recolour their layers without re-implementing the
   key or the persistence. A matching pre-paint snippet in each page's <head>
   applies the saved choice before first render, so there is no flash. */
(function () {
  var root = document.documentElement;
  var THEME_KEY = 'atlas-theme';
  var ICONS = {
    dark: '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 3a6.5 6.5 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>',
    light: '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 4.5v-2M12 21.5v-2M4.5 12h-2M21.5 12h-2M5.6 5.6 4.2 4.2M19.8 19.8l-1.4-1.4M18.4 5.6l1.4-1.4M4.2 19.8l1.4-1.4"/><circle cx="12" cy="12" r="4.5"/></svg>'
  };

  function systemTheme() {
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }

  function effective() {
    return root.dataset.theme || systemTheme();
  }

  function hasSavedTheme() {
    try { return !!localStorage.getItem(THEME_KEY); } catch (e) { return false; }
  }

  function syncControls() {
    var theme = effective();
    var next = theme === 'dark' ? 'light' : 'dark';
    document.querySelectorAll('#theme').forEach(function (btn) {
      btn.innerHTML = ICONS[next];
      btn.setAttribute('aria-label', 'Switch to ' + next + ' theme');
      btn.setAttribute('title', 'Switch to ' + next + ' theme');
    });
  }

  function setTheme(theme, persist) {
    root.dataset.theme = theme;
    if (persist) {
      try { localStorage.setItem(THEME_KEY, theme); } catch (e) {}
    }
    syncControls();
    document.dispatchEvent(new CustomEvent('atlas:themechange', { detail: { theme: theme } }));
  }

  function apply(theme) {
    setTheme(theme, true);
  }

  function toggleFrom(event) {
    var btn = event.target && event.target.closest ? event.target.closest('#theme') : null;
    if (!btn) return;
    event.preventDefault();
    apply(effective() === 'dark' ? 'light' : 'dark');
  }

  function wire() {
    if (!root.dataset.theme) setTheme(systemTheme(), false);
    syncControls();
    document.addEventListener('DOMContentLoaded', syncControls);
    document.addEventListener('atlas:mastheadrendered', syncControls);
    document.addEventListener('click', toggleFrom);
    document.addEventListener('keydown', function (event) {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      var btn = event.target && event.target.closest ? event.target.closest('#theme') : null;
      if (!btn) return;
      event.preventDefault();
      apply(effective() === 'dark' ? 'light' : 'dark');
    });
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', function () {
        if (!hasSavedTheme()) setTheme(systemTheme(), false);
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wire);
  } else {
    wire();
  }
})();
