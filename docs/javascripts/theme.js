document.addEventListener("DOMContentLoaded", () => {
  const storageKey = "agentseek-docs-theme";
  const root = document.documentElement;
  const button = document.getElementById("theme-toggle");
  const label = button?.querySelector(".theme-toggle-label");

  const applyTheme = (theme) => {
    root.setAttribute("data-theme", theme);
    if (button) {
      const nextTheme = theme === "dark" ? "light" : "dark";
      button.dataset.nextTheme = nextTheme;
      button.setAttribute("aria-label", `Switch to ${nextTheme} mode`);
      button.setAttribute("title", `Switch to ${nextTheme} mode`);
      if (label) {
        label.textContent = `Switch to ${nextTheme} mode`;
      }
    }
  };

  const currentTheme = root.getAttribute("data-theme") || "light";
  applyTheme(currentTheme);

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
