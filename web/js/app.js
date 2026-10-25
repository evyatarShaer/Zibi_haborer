// Router: "#/" input screen; "#/h/{id}" waiting screen, then the verdict. A hearing
// just submitted from this tab gets the full story; a reopened link of a decided
// hearing goes straight to the verdict.
import { inputScreen } from "./input.js";
import { verdict } from "./verdict.js";
import { waiting } from "./waiting.js";
import { load, save } from "./session.js";

const root = document.getElementById("app");
let cleanup = () => {};

const goNew = () => { location.hash = "#/"; };
const goHearing = (id) => {
  save("fresh", id);
  location.hash = `#/h/${id}`;
};

function route() {
  cleanup();
  window.scrollTo(0, 0);
  const m = location.hash.match(/^#\/h\/([\w-]+)$/);
  if (!m) {
    cleanup = inputScreen(root, goHearing);
    return;
  }
  const id = m[1];
  const fresh = load("fresh") === id;
  save("fresh", null);
  cleanup = waiting(root, id, fresh, {
    onNew: goNew,
    onSubmitted: goHearing,
    onVerdict: (h) => { cleanup = verdict(root, h, goNew); },
  });
}

window.addEventListener("hashchange", route);
route();
