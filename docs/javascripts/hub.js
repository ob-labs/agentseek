document.addEventListener("DOMContentLoaded", () => {
  for (const hub of document.querySelectorAll(".hub-page")) {
    const searchInput = hub.querySelector("[data-hub-search]");
    const tabs = Array.from(hub.querySelectorAll("[data-hub-tab]"));
    const sections = Array.from(hub.querySelectorAll("[data-hub-category]"));
    const cards = Array.from(hub.querySelectorAll(".hub-card"));
    const shownCount = hub.querySelector("[data-hub-shown]");
    const totalCount = hub.querySelector("[data-hub-total]");
    const emptyState = hub.querySelector("[data-hub-empty]");

    if (!searchInput || !shownCount || !totalCount || !emptyState) {
      continue;
    }

    let activeCategory = "all";

    const updateCounters = () => {
      if (totalCount) {
        totalCount.textContent = String(cards.length);
      }
    };

    const applyFilters = () => {
      const query = searchInput.value.trim().toLowerCase();
      let shown = 0;

      for (const section of sections) {
        const categoryName = section.getAttribute("data-hub-category");
        const categoryMatch = activeCategory === "all" || categoryName === activeCategory;
        section.hidden = !categoryMatch;

        if (!categoryMatch) {
          continue;
        }

        const sectionCards = Array.from(section.querySelectorAll(".hub-card"));
        let sectionVisible = 0;
        for (const card of sectionCards) {
          const searchText = (card.getAttribute("data-search") || "").toLowerCase();
          const queryMatch = query === "" || searchText.includes(query);
          card.hidden = !queryMatch;
          if (queryMatch) {
            shown += 1;
            sectionVisible += 1;
          }
        }
        section.hidden = sectionVisible === 0;
      }

      shownCount.textContent = String(shown);
      emptyState.hidden = shown !== 0;
    };

    for (const tab of tabs) {
      tab.addEventListener("click", () => {
        for (const other of tabs) {
          other.classList.remove("active");
        }
        tab.classList.add("active");
        activeCategory = tab.getAttribute("data-hub-tab") || "all";
        applyFilters();
      });
    }

    searchInput.addEventListener("input", applyFilters);

    hub.addEventListener("click", async (event) => {
      const button = event.target instanceof Element ? event.target.closest("[data-copy-cmd]") : null;
      if (!(button instanceof HTMLButtonElement)) {
        return;
      }

      const command = button.getAttribute("data-copy-cmd");
      if (!command || !navigator.clipboard) {
        return;
      }

      await navigator.clipboard.writeText(command);
      const originalText = button.textContent;
      button.textContent = "Copied";
      window.setTimeout(() => {
        button.textContent = originalText;
      }, 1200);
    });

    updateCounters();
    applyFilters();
  }
});
