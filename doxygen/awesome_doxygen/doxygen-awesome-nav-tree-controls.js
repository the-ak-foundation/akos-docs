// SPDX-License-Identifier: MIT
// Add "Expand all" and "Collapse all" controls for the Doxygen nav tree.
(function () {
  function clickAll(selector) {
    var toggles = document.querySelectorAll(selector);
    for (var i = 0; i < toggles.length; i += 1) {
      toggles[i].click();
    }
    return toggles.length;
  }

  function expandAll() {
    var maxRounds = 30;
    var round = 0;

    function step() {
      round += 1;
      var count = clickAll("#nav-tree span.arrowhead.closed");
      if (count > 0 && round < maxRounds) {
        window.setTimeout(step, 40);
      }
    }

    step();
  }

  function collapseAll() {
    clickAll("#nav-tree span.arrowhead.opened");
  }

  function injectControls() {
    var container = document.getElementById("nav-tree-contents");
    if (!container || document.getElementById("nav-tree-controls")) return;

    var controls = document.createElement("div");
    controls.id = "nav-tree-controls";
    controls.className = "nav-tree-controls";

    var expandBtn = document.createElement("button");
    expandBtn.type = "button";
    expandBtn.className = "nav-tree-control-btn";
    expandBtn.textContent = "Expand all";
    expandBtn.title = "Expand all navigation sections";
    expandBtn.addEventListener("click", expandAll);

    var collapseBtn = document.createElement("button");
    collapseBtn.type = "button";
    collapseBtn.className = "nav-tree-control-btn";
    collapseBtn.textContent = "Collapse all";
    collapseBtn.title = "Collapse all navigation sections";
    collapseBtn.addEventListener("click", collapseAll);

    controls.appendChild(expandBtn);
    controls.appendChild(collapseBtn);
    container.insertBefore(controls, container.firstChild);
  }

  function attachAutoExpandOnLabelClick() {
    var navTree = document.getElementById("nav-tree");
    if (!navTree || navTree.dataset.autoExpandBound === "1") return;

    navTree.addEventListener("click", function (event) {
      var link = event.target.closest(".item .label a");
      if (!link) return;

      // Keep browser default behavior for modified clicks (new tab, etc.).
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      if (event.button !== 0) return;

      var item = link.closest(".item");
      if (!item) return;

      // If this item has a closed expand arrow, expand first.
      var closedArrow = item.querySelector(".arrowhead.closed");
      if (!closedArrow) return;

      var toggleLink = closedArrow.closest("a");
      if (!toggleLink) return;

      // Expand the node immediately, but keep default link navigation.
      // This lets one click both open children and navigate to the page/anchor.
      toggleLink.click();
    });

    navTree.dataset.autoExpandBound = "1";
  }

  function expandSelectedNode() {
    var selectedItem = document.querySelector("#nav-tree .item.selected, #nav-tree #selected");
    if (!selectedItem) return false;

    var closedArrow = selectedItem.querySelector(".arrowhead.closed");
    if (!closedArrow) return true;

    var toggleLink = closedArrow.closest("a");
    if (!toggleLink) return true;

    toggleLink.click();
    return true;
  }

  function expandCurrentPageNode() {
    var navTree = document.getElementById("nav-tree");
    if (!navTree) return false;

    var page = window.location.pathname.split("/").pop();
    if (!page) return false;

    var links = navTree.querySelectorAll(".item .label a[href]");
    for (var i = 0; i < links.length; i += 1) {
      var href = links[i].getAttribute("href");
      if (!href) continue;
      if (!(href === page || href.indexOf(page + "#") === 0)) continue;

      var item = links[i].closest(".item");
      if (!item) return true;

      var closedArrow = item.querySelector(".arrowhead.closed");
      if (!closedArrow) return true;

      var toggleLink = closedArrow.closest("a");
      if (!toggleLink) return true;

      toggleLink.click();
      return true;
    }

    return false;
  }

  function init() {
    // Nav tree is built after page scripts run, so retry briefly until present.
    var tries = 0;
    var maxTries = 60;

    function tryInject() {
      injectControls();
      attachAutoExpandOnLabelClick();
      // Keep retrying briefly so selected node can be expanded after nav tree finishes rendering.
      expandSelectedNode();
      expandCurrentPageNode();

      if (tries < maxTries) {
        tries += 1;
        window.setTimeout(tryInject, 50);
      }
    }

    tryInject();
  }

  if (document.readyState === "loading") {
    window.addEventListener("load", init);
  } else {
    init();
  }
})();
