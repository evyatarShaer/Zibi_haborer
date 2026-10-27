// A personal page, /a/{token} or /b/{token} (SPEC §3, §15): polls the case and shows the
// screen flow.screen() picks. B's link is bound to a device only when B submits (any
// browser may open it before that). The highest hearing this device has shown is
// remembered, so a verdict it has not seen is replayed once.
import { getMine, postAppeal } from "./api.js";
import { T } from "./copy.js";
import { screen } from "./flow.js";
import { noticeScreen } from "./notice.js";
import { waitAScreen, writeBScreen } from "./pending.js";
import { recall, remember } from "./session.js";
import { verdictScreen } from "./verdict.js";
import { storyScreen } from "./waiting.js";

const STORY_POLL_MS = 700;
const POLL_MS = 3000;

export function casePage(root, side, token) {
  let view = null, current = null, key = "", stopped = false, timer = null;
  const seenKey = () => `seen:${view.id}`;
  const publicUrl = () => `${location.origin}/c/${view.id}`;

  function make(s) {
    if (s.kind === "error") return noticeScreen(root, view.error_message, "error");
    if (s.kind === "waitA") return waitAScreen(root, view);
    if (s.kind === "writeB") return writeBScreen(root, view, token, accept);
    if (s.kind === "story") {
      return storyScreen(root, view, s.n, () => { remember(seenKey(), s.n); render(); });
    }
    remember(seenKey(), s.n);
    return verdictScreen(root, view, s.n, { onAppeal, publicUrl: publicUrl() });
  }

  function render() {
    const s = screen(view, recall(seenKey(), -1));
    const k = `${s.kind}:${s.n}:${view.can_appeal}`;
    if (k === key) return current.update(view);
    if (current) current.stop();
    key = k;
    current = make(s);
    window.scrollTo(0, 0);
  }

  function accept(data) {
    view = data;
    render();
  }

  async function onAppeal() {
    const r = await postAppeal(side, token);
    if (r.status === 201) return accept(r.data) || null;
    return r.status === 0 ? T.noConnection : r.data.error || T.failed;
  }

  function end(message, kind) {
    stopped = true;
    if (current) current.stop();
    current = noticeScreen(root, message, kind);
  }

  // A network error keeps the current screen and tries again on the next poll.
  function answer(r) {
    if (r.status === 200) return accept(r.data);
    if (r.status === 404) return end(T.closed, "closed");
    if (r.status === 403) return end(T.taken, "taken");
    if (r.status === 409) return end(T.ownLink, "own");
  }

  async function poll(first) {
    answer(await first());
    if (!stopped) timer = setTimeout(() => poll(() => getMine(side, token)),
      key.startsWith("story") ? STORY_POLL_MS : POLL_MS);
  }

  poll(() => getMine(side, token));
  return () => {
    stopped = true;
    clearTimeout(timer);
    if (current) current.stop();
  };
}
