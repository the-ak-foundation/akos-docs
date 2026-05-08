// SPDX-License-Identifier: MIT
// Force navtree sync ON so the sidebar highlight follows page navigation.
(function () {
  function enableSync() {
    var navSync = document.getElementById("nav-sync");
    if (!navSync) return;
    navSync.classList.add("sync");
    try {
      localStorage.removeItem("link");
    } catch (e) {
      // Ignore storage errors.
    }
  }

  if (document.readyState === "loading") {
    window.addEventListener("load", enableSync);
  } else {
    enableSync();
  }
})();
