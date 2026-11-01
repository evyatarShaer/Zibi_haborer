// Icons (DECISIONS 2026-10-29): Lucide (ISC licence, lucide.dev) shapes inlined, plus a
// chat-bubble-and-phone glyph for WhatsApp buttons. 24 × 24, stroked in currentColor.
import { svg } from "./dom.js";

const P = (d) => ["path", { d }];
const C = (cx, cy, r) => ["circle", { cx, cy, r }];
const PHONE = "M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67" +
  "A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6" +
  "l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z";

export const ICONS = {
  moon: [P("M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z")],
  sun: [C(12, 12, 4), P("M12 2v2M12 20v2m-7.07-17.07 1.41 1.41m11.32 11.32 1.41 1.41M2 12h2m16 0h2" +
    "M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41")],
  help: [C(12, 12, 10), P("M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"), P("M12 17h.01")],
  scale: [P("m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"), P("m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"),
    P("M7 21h10M12 3v18M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2")],
  gavel: [P("m14.5 12.5-8 8a2.119 2.119 0 1 1-3-3l8-8"), P("m16 16 6-6m-14-2 6-6m-5 5 8 8m4-4-8-8")],
  share: [C(18, 5, 3), C(6, 12, 3), C(18, 19, 3), P("m8.59 13.51 6.83 3.98m-.01-10.98-6.82 3.98")],
  again: [P("M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"), P("M3 3v5h5")],
  alert: [P("m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"), P("M12 9v4M12 17h.01")],
  check: [P("M20 6 9 17l-5-5")],
  plus: [P("M5 12h14M12 5v14")],
  pulse: [P("M22 12h-4l-3 9L9 3l-3 9H2")],
  flag: [P("M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"), P("M4 22v-7")],
  send: [P("m22 2-7 20-4-9-9-4Z"), P("M22 2 11 13")],
  clock: [C(12, 12, 10), P("M12 6v6l4 2")],
  wifiOff: [P("M12 20h.01M8.5 16.43a5 5 0 0 1 7 0M5 12.86a10 10 0 0 1 5.17-2.69M19 12.86a10 10 0 0 0-2-1.54" +
    "M2 8.82a15 15 0 0 1 4.18-2.65M22 8.82a15 15 0 0 0-11.29-3.76M2 2l20 20")],
  whatsapp: [P("M7.9 20A9 9 0 1 0 4 16.1L2 22Z"), ["path", { d: PHONE, transform: "translate(6.9 6.9) scale(.42)" }]],
};

export const icon = (name, cls = "icon") =>
  svg("svg", { class: cls, viewBox: "0 0 24 24", "aria-hidden": "true", focusable: "false" },
    ICONS[name].map(([tag, attrs]) => svg(tag, attrs)));
