// Day / night court (DECISIONS 2026-10-29). The page follows the system setting until the
// header toggle picks one; the choice is saved per device. index.html's head script applies
// the same rule before the first paint, so the wrong theme never flashes.
import { el } from "./dom.js";
import { icon } from "./icons.js";
import { T } from "./copy.js";
import { recall, remember } from "./session.js";

const KEY = "theme";
const system = () => matchMedia("(prefers-color-scheme: dark)");
const apply = () => {
  document.documentElement.dataset.theme = recall(KEY, null) || (system().matches ? "dark" : "light");
};
export const isDark = () => document.documentElement.dataset.theme === "dark";

export function themeToggle() {
  const button = el("button", { type: "button", class: "icon-button theme-toggle", "aria-label": T.nightMode });
  const draw = () => {
    button.setAttribute("aria-pressed", String(isDark()));
    button.replaceChildren(icon(isDark() ? "sun" : "moon"));
  };
  button.addEventListener("click", () => {
    remember(KEY, isDark() ? "light" : "dark");
    apply();
    draw();
  });
  system().addEventListener("change", () => { apply(); draw(); });
  apply();
  draw();
  return button;
}
