// Forms (SPEC §3, §15.2): A opens a case (topic, both names, A's argument); B writes
// blind. Live letter counters; submit stays disabled until the fields are valid; the
// server checks the same rules (and the word filter) and its Hebrew messages show under
// the fields.
import { el, show } from "./dom.js";
import { openCase } from "./api.js";
import { T } from "./copy.js";
import { MAX_CHARS, MIN_LETTERS, argumentOk, chars, hebrewLetters } from "./letters.js";

const MAX_NAME = 30;
const MAX_TOPIC = 80;

export function field(label, input, hint) {
  const error = el("p", { class: "error", "aria-live": "polite" });
  return { error, input, node: el("label", { class: "field" }, label, input, hint, error) };
}

// An argument box with its counter; valid() follows the §3 rule.
export function argumentField(label, name) {
  const text = el("textarea", { name, rows: 4, placeholder: T.argumentPlaceholder });
  const count = el("p", { class: "counter" });
  const update = () => {
    const n = hebrewLetters(text.value);
    count.textContent = `${T.letters(Math.min(n, MIN_LETTERS), MIN_LETTERS)} · ${T.chars(chars(text.value), MAX_CHARS)}`;
    count.classList.toggle("ok", argumentOk(text.value));
  };
  text.addEventListener("input", update);
  update();
  return { ...field(label, text, count), valid: () => argumentOk(text.value) };
}

// A form whose submit(body) resolves to {errors} / {message} or never (it navigated).
export function form(fields, button, collect, submit, busy = T.opening) {
  const message = el("p", { class: "error", "aria-live": "polite" });
  const label = button.textContent;
  const refresh = () => { button.disabled = !Object.values(fields).every((f) => !f.valid || f.valid()); };
  const node = el("form", { class: "card", novalidate: true, oninput: refresh },
    Object.values(fields).map((f) => f.node), button, message);
  node.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (button.disabled) return;
    button.disabled = true;
    button.textContent = busy;
    const out = await submit(collect());
    const errors = out.errors || {};
    for (const [k, f] of Object.entries(fields)) f.error.textContent = errors[k] || "";
    message.textContent = out.message || "";
    button.textContent = label;
    refresh();
  });
  refresh();
  return node;
}

// The server's answer as form feedback; 2xx goes to `onOk(data)`.
export function feedback(r, onOk) {
  if (r.status >= 200 && r.status < 300) return onOk(r.data) || new Promise(() => {});
  if (r.status === 422) return { errors: r.data.errors || {} };
  if (r.status === 0) return { message: T.noConnection };
  return { message: r.data.error || T.failed };
}

export function openCaseScreen(root) {
  const nonEmpty = (input) => () => input.value.trim() !== "";
  const name = (label, key) => {
    const f = field(label, el("input", { name: key, maxlength: MAX_NAME, autocomplete: "off" }));
    return { ...f, valid: nonEmpty(f.input) };
  };
  const fields = {
    topic: field(T.topic, el("input", { name: "topic", maxlength: MAX_TOPIC }),
      el("p", { class: "hint" }, T.topicHint)),
    name_a: name(T.yourName, "name_a"), name_b: name(T.otherName, "name_b"),
    text_a: argumentField(T.yourArgument, "text_a"),
  };
  fields.text_a.node.append(el("p", { class: "hint" }, T.blindHint));
  const collect = () => Object.fromEntries(Object.entries(fields).map(([k, f]) => [k, f.input.value]));
  const submit = async (body) => feedback(await openCase(body), (d) => { location.assign(d.link_a); });
  show(root, el("p", { class: "tagline" }, T.tagline),
    form(fields, el("button", { type: "submit", class: "primary" }, T.open), collect, submit));
  return { update: () => {}, stop: () => {} };
}
