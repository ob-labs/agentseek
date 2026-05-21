document.addEventListener("DOMContentLoaded", () => {
  const storageKey = "agentseek-docs-theme";
  const root = document.documentElement;
  const locale = document.body?.dataset.locale === "zh" ? "zh" : "en";
  const button = document.getElementById("theme-toggle");
  const label = button?.querySelector(".theme-toggle-label");
  const themeLabels = {
    en: {
      light: "Switch to light mode",
      dark: "Switch to dark mode",
    },
    zh: {
      light: "切换到浅色模式",
      dark: "切换到深色模式",
    },
  };
  const searchLabels = {
    en: {
      title: "Search",
      inputLabel: "Type to start searching",
      inputTitle: "Please enter search terms here",
      noResults: "No document matches found",
      close: "Close",
    },
    zh: {
      title: "搜索",
      inputLabel: "输入关键字开始搜索",
      inputTitle: "请输入搜索关键字",
      noResults: "没有找到匹配的文档",
      close: "关闭",
    },
  };

  const applyTheme = (theme) => {
    root.setAttribute("data-theme", theme);
    if (button) {
      const nextTheme = theme === "dark" ? "light" : "dark";
      const nextThemeLabel = themeLabels[locale][nextTheme];
      button.dataset.nextTheme = nextTheme;
      button.setAttribute("aria-label", nextThemeLabel);
      button.setAttribute("title", nextThemeLabel);
      if (label) {
        label.textContent = nextThemeLabel;
      }
    }
  };

  const currentTheme = root.getAttribute("data-theme") || "light";
  applyTheme(currentTheme);

  const modalTitle = document.getElementById("searchModalLabel");
  const inputLabel = document.getElementById("searchInputLabel");
  const searchInput = document.getElementById("mkdocs-search-query");
  const searchResults = document.getElementById("mkdocs-search-results");
  const closeButton = document.querySelector("#mkdocs_search_modal [data-dismiss='modal']");
  const modalCopy = searchLabels[locale];

  if (modalTitle) {
    modalTitle.textContent = modalCopy.title;
  }
  if (inputLabel) {
    inputLabel.textContent = modalCopy.inputLabel;
  }
  if (searchInput) {
    searchInput.setAttribute("title", modalCopy.inputTitle);
  }
  if (searchResults) {
    searchResults.setAttribute("data-no-results-text", modalCopy.noResults);
  }
  if (closeButton) {
    closeButton.setAttribute("aria-label", modalCopy.close);
  }

  if (!button) {
    return;
  }

  button.addEventListener("click", () => {
    const nextTheme = (root.getAttribute("data-theme") || "light") === "dark" ? "light" : "dark";
    try {
      localStorage.setItem(storageKey, nextTheme);
    } catch (e) {}
    applyTheme(nextTheme);
  });
});
