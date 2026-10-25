// Input screen (SPEC §14.1, P2A-4): optional topic, two sides with a name and an
// argument, live letter counters. Submit stays disabled until both sides are valid;
// the server checks the same rules and its Hebrew messages show under the fields.
import { el, show } from "./dom.js";
import { postHearing } from "./api.js";
import { T } from "./copy.js";
import { MAX_CHARS, MIN_LETTERS, argumentOk, chars, hebrewLetters } from "./letters.js";
import { load, save } from "./session.js";

const MAX_NAME = 30;
const MAX_TOPIC = 80;

function field(label, input, hint) {
  const error = el("p", { class: "error", "aria-live": "polite" });
  return { error, input, node: el("label", { class: "field" }, label, input, hint, error) };
}

function side(key, draft) {
  const name = el("input", { maxlength: MAX_NAME, autocomplete: "off", value: draft[`name_${key}`] || "" });
  const text = el("textarea", { rows: 4, placeholder: "למה אני צודק/ת…" });
  text.value = draft[`text_${key}`] || "";
  const count = el("p", { class: "counter" });
  const f = { name: field(T.name, name), text: field(T.argument, text, count) };
  const update = () => {
    const n = hebrewLetters(text.value);
    count.textContent = `${T.letters(Math.min(n, MIN_LETTERS), MIN_LETTERS)} · ${T.chars(chars(text.value), MAX_CHARS)}`;
    count.classList.toggle("ok", argumentOk(text.value));
  };
  text.addEventListener("input", update);
  update();
  const node = el("fieldset", { class: `side side-${key}` }, el("legend", {}, T.side[key]),
    f.name.node, f.text.node);
  return { node, f, valid: () => name.value.trim() !== "" && argumentOk(text.value) };
}

// Submits a hearing body; the caller navigates on success. -> {id} or {errors, message}.
export async function submit(body) {
  const r = await postHearing(body);
  if (r.status === 201) {
    save("lastBody", body);
    save("names", { name_a: body.name_a, name_b: body.name_b });
    return { id: r.data.id };
  }
  if (r.status === 422) return { errors: r.data.errors || {} };
  if (r.status === 503) return { message: r.data.error };
  return { message: r.status === 0 ? T.noConnection : T.failed };
}

export function inputScreen(root, onSubmitted) {
  const draft = load("draft") || load("names") || {};
  save("draft", null);
  const topic = field(T.topic, el("input", { maxlength: MAX_TOPIC, value: draft.topic || "" }),
    el("p", { class: "hint" }, T.topicHint));
  const sides = { a: side("a", draft), b: side("b", draft) };
  const button = el("button", { type: "submit", class: "primary" }, T.submit);
  const message = el("p", { class: "error", "aria-live": "polite" });
  const refresh = () => { button.disabled = !(sides.a.valid() && sides.b.valid()); };
  const form = el("form", { class: "card", novalidate: true, oninput: refresh },
    topic.node, sides.a.node, sides.b.node, button, message);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (button.disabled) return;
    const body = { topic: topic.input.value, name_a: sides.a.f.name.input.value,
      text_a: sides.a.f.text.input.value, name_b: sides.b.f.name.input.value,
      text_b: sides.b.f.text.input.value };
    button.disabled = true;
    button.textContent = T.sending;
    const out = await submit(body);
    if (out.id) return onSubmitted(out.id);
    const errors = out.errors || {};
    topic.error.textContent = errors.topic || "";
    for (const k of ["a", "b"]) {
      sides[k].f.name.error.textContent = errors[`name_${k}`] || "";
      sides[k].f.text.error.textContent = errors[`text_${k}`] || "";
    }
    message.textContent = out.message || "";
    button.textContent = T.submit;
    refresh();
  });
  show(root, el("p", { class: "tagline" }, T.tagline), form);
  refresh();
  return () => {};
}
