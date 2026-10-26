"""The court (SPEC §14.7, §15.9): one hearing at a time, taken in order from the DB.

A hearing is filed by the case store, which refuses a new one with Busy while one runs
and MAX_WAITING more wait. The worker thread takes the oldest queued hearing: queued →
running → decided, or failed if the simulation raised. Queued hearings live in the DB, so
after a restart they simply run (a running one is re-queued first, cases.Store.requeue).
The deadline sweep files the plain-water hearing of every case B left unanswered.
"""
import logging
import secrets
import threading

from borer_api.cases import Busy, Closed

MAX_WAITING = 3
MAX_ACTIVE = 1 + MAX_WAITING
BUSY = "הזבוב עסוק בתיקים אחרים כרגע. נסו שוב בעוד דקה"

log = logging.getLogger(__name__)


def new_seed() -> int:
    """A fresh random hearing seed (and so a fresh mood)."""
    return secrets.randbelow(2 ** 31)


class Court:
    def __init__(self, store, runner):
        """runner(text_a, text_b, seed, wait_h) -> borer_sim.hearing.run result
        (text_b None = plain water)."""
        self.store, self.runner = store, runner
        self._wake, self._stop = threading.Event(), False
        threading.Thread(target=self._work, name="court", daemon=True).start()

    def wake(self) -> None:
        """A hearing was filed."""
        self._wake.set()

    def _work(self) -> None:
        while not self._stop:
            self._wake.clear()
            h = self.store.next_queued()
            if h is None:
                self._wake.wait(1.0)
            elif not self._stop:
                self._hear(h)

    def _hear(self, h: dict) -> None:
        """One hearing; any error fails this hearing only, never the worker thread."""
        try:
            self.store.start(h["id"])
            self.store.finish(h["id"], self.runner(h["text_a"], h["text_b"], h["seed"], h["wait_h"]))
        except Exception:
            log.exception("hearing %s failed", h["id"])
            try:
                self.store.fail(h["id"])
            except Exception:
                log.exception("could not mark hearing %s failed", h["id"])

    def sweep(self) -> int:
        """File the no-show hearing of each case past its deadline; returns how many.
        When the court is full the rest wait for the next sweep."""
        filed = 0
        for cid in self.store.due():
            try:
                self.store.no_show(cid, new_seed())
            except Closed:  # B submitted meanwhile
                continue
            except Busy:
                break
            filed += 1
            self.wake()
        return filed

    def sweep_loop(self, stop: threading.Event, every_s: float) -> None:
        """Sweep at once (catching up after a restart), then every `every_s` until `stop`."""
        while True:
            try:
                self.sweep()
            except Exception:
                log.exception("deadline sweep failed")
            if stop.wait(every_s):
                return

    def close(self) -> None:
        """Stop after the current hearing; queued ones run after the next startup."""
        self._stop = True
        self._wake.set()
