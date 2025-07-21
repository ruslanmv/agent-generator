// ────────────────────────────────────────────────────────────────
//  src/agent_generator/web/static/js/graph.js
// ────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", function () {
  if (typeof mermaid !== "undefined") {
    mermaid.initialize({
      startOnLoad: true,
      theme: "neutral",
      flowchart: { curve: "basis" },
      securityLevel: "loose"
    });
  } else {
    console.warn("Mermaid library not loaded; diagrams will not render.");
  }
});
// ────────────────────────────────────────────────────────────────
//  src/agent_generator/web/static/js/graph.js
// ────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", function () {
  if (typeof mermaid !== "undefined") {
    mermaid.initialize({
      startOnLoad: true,
      theme: "neutral",
      flowchart: { curve: "basis" },
      securityLevel: "loose"
    });
  } else {
    console.warn("Mermaid library not loaded; diagrams will not render.");
  }
});
