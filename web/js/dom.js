// el("p", {class: "x", onclick: f}, "text", child): strings become text nodes, so user
// input never reaches innerHTML. svg(...) is the same for SVG elements.
const SVG_NS = "http://www.w3.org/2000/svg";

function make(node, props, children) {
  for (const [k, v] of Object.entries(props || {})) {
    if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else if (v === true) node.setAttribute(k, "");
    else if (v !== false && v !== null && v !== undefined) node.setAttribute(k, v);
  }
  for (const c of children.flat()) {
    if (c !== null && c !== undefined && c !== false) {
      node.append(typeof c === "string" || typeof c === "number" ? String(c) : c);
    }
  }
  return node;
}

export const el = (tag, props, ...children) => make(document.createElement(tag), props, children);
export const svg = (tag, props, ...children) => make(document.createElementNS(SVG_NS, tag), props, children);

export function show(root, ...nodes) {
  root.replaceChildren(...nodes);
}
