// Turns ```mermaid blocks (rendered as <pre class="diagram">) into SVG diagrams.
// Uses the local assets/mermaid.min.js: no internet needed. Follows the light/dark toggle.
(function () {
  function theme() {
    return document.body.getAttribute("data-md-color-scheme") === "slate" ? "dark" : "default";
  }
  function draw() {
    if (!window.mermaid) return;
    document.querySelectorAll("pre.diagram").forEach(function (pre) {
      var div = document.createElement("div");
      div.className = "mermaid";
      div.dataset.source = pre.textContent;
      pre.replaceWith(div);
    });
    var diagrams = document.querySelectorAll("div.mermaid");
    if (!diagrams.length) return;
    diagrams.forEach(function (div) {
      div.removeAttribute("data-processed");
      div.textContent = div.dataset.source;
    });
    window.mermaid.initialize({ startOnLoad: false, theme: theme() });
    window.mermaid.run({ nodes: diagrams });
  }
  function start() {
    draw();
    // redraw with the matching theme when the reader toggles light/dark
    new MutationObserver(draw).observe(document.body, { attributeFilter: ["data-md-color-scheme"] });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
