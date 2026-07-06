/* masthead.js — the single source of truth for global site navigation.
   ----------------------------------------------------------------------------
   The atlas is a hybrid: the city consoles are a full-screen map *app* (nav
   lives in the left rail) while Why / Findings / About / Home are editorial
   *pages* (nav is a top bar). So this renders ONE nav model in TWO layout
   variants. Edit the SECTIONS / identity here once and every surface updates.

   Identity (see also the project naming convention):
     "The Unelected City" .... the project / masthead wordmark
     "Accountability Atlas" ... the maps tool (the Atlas section)
     "Part IXA · 74th Amdt" ... the constitutional kicker (not a name)

   Usage:
     <header data-masthead="bar"></header>     (editorial pages — top bar)
     <header data-masthead="rail"></header>    (console — inside the rail)
     <script src="<base>/assets/masthead.js"></script>   (classic, not defer)

   The script locates its own URL synchronously to derive the site base, so the
   links resolve at any page depth and under any deploy path. */
(function () {
  // currentScript is only valid during synchronous evaluation — capture now.
  var self = document.currentScript;
  var base = (self && self.src ? self.src : "").replace(/assets\/masthead\.js.*$/, "");

  // The interrogative grammar of the site (poses questions; never a CTA).
  var SECTIONS = [
    { label: "Atlas",    href: "cities/",            match: /\/cities\//,                title: "Explore your city on the map" },
    { label: "Why",      href: "why/",               match: /\/why\//,                   title: "Why is your city governed this way?" },
    { label: "Findings", href: "findings/",          match: /\/(findings|devolution|labour)\//, title: "What the data shows" },
    { label: "About",    href: "about/",             match: /\/about\//,                 title: "What this is, and how to read it" },
  ];

  var SUN = '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 3a6.5 6.5 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>';

  function esc(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function navHtml(activeIdx) {
    return SECTIONS.map(function (s, i) {
      var cls = i === activeIdx ? ' class="is-active" aria-current="page"' : "";
      return '<a' + cls + ' href="' + base + esc(s.href) + '" title="' + esc(s.title) + '">' + esc(s.label) + "</a>";
    }).join("");
  }

  function render(el) {
    var variant = el.getAttribute("data-masthead") || "bar";
    var path = location.pathname;
    var activeIdx = -1;
    SECTIONS.forEach(function (s, i) { if (s.match.test(path)) activeIdx = i; });

    var brand =
      '<a class="mh-brand" href="' + base + 'index.html" aria-label="The Unelected City — home">' +
        '<img class="mh-mark" src="' + base + 'assets/ixa-mark.png" alt="" aria-hidden="true">' +
        '<span class="mh-word"><span>The Unelected City</span>' +
          '<b>Part IXA · the 74th Amendment</b></span>' +
      "</a>";

    // The console rail already carries its own theme toggle; the bar owns one.
    var toggle = variant === "rail" ? "" :
      '<button class="mh-theme" id="theme" type="button" aria-label="Toggle light or dark theme" title="Toggle theme">' + SUN + "</button>";

    el.className = "mh mh--" + variant;
    el.innerHTML =
      brand +
      '<nav class="mh-nav" aria-label="Site">' + navHtml(activeIdx) + "</nav>" +
      toggle;
  }

  function init() {
    var nodes = document.querySelectorAll("[data-masthead]");
    for (var i = 0; i < nodes.length; i++) render(nodes[i]);
    document.dispatchEvent(new CustomEvent("atlas:mastheadrendered"));
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
