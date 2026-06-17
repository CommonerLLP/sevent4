/* theme.js — wires the manual light/dark toggle for the WHY layer.
   Default comes from the OS via @media (prefers-color-scheme) in CSS; this only
   handles the user's manual override (persisted), per org design rule 6.
   The pre-paint <head> snippet applies any saved choice before first render. */
(function () {
  var root = document.documentElement;
  function effective() {
    if (root.dataset.theme) return root.dataset.theme;
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }
  function wire() {
    var btn = document.getElementById('theme');
    if (!btn) return;
    btn.addEventListener('click', function () {
      var next = effective() === 'dark' ? 'light' : 'dark';
      root.dataset.theme = next;
      try { localStorage.setItem('sevent4-theme', next); } catch (e) {}
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wire);
  } else {
    wire();
  }
})();
