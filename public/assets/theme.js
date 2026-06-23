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

  function effective() {
    if (root.dataset.theme) return root.dataset.theme;
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }

  function apply(theme) {
    root.dataset.theme = theme;
    try { localStorage.setItem(THEME_KEY, theme); } catch (e) {}
    document.dispatchEvent(new CustomEvent('atlas:themechange', { detail: { theme: theme } }));
  }

  function toggleFrom(event) {
    var btn = event.target && event.target.closest ? event.target.closest('#theme') : null;
    if (!btn) return;
    event.preventDefault();
    apply(effective() === 'dark' ? 'light' : 'dark');
  }

  function wire() {
    document.addEventListener('click', toggleFrom);
    document.addEventListener('keydown', function (event) {
      if (event.key !== 'Enter' && event.key !== ' ') return;
      var btn = event.target && event.target.closest ? event.target.closest('#theme') : null;
      if (!btn) return;
      event.preventDefault();
      apply(effective() === 'dark' ? 'light' : 'dark');
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wire);
  } else {
    wire();
  }
})();
