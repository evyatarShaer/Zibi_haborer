"""The court: one hearing at a time; up to MAX_WAITING more wait in line (SPEC §14).

The caller creates the stored row, then submit()s its id; when the line is full submit
raises Busy (the caller drops the row and answers 503). One worker thread takes hearings
in order: queued → running → decided, or failed if the simulation raised.
"""
import logging
import queue
import threading

MAX_WAITING = 3
BUSY = "הזבוב עסוק בתיקים אחרים כרגע. נסו שוב בעוד דקה"

log = logging.getLogger(__name__)


class Busy(Exception):
    pass


class Court:
    def __init__(self, store, runner, max_waiting: int = MAX_WAITING):
        """runner(text_a, text_b, seed) -> borer_sim.hearing.run result."""
        self.store, self.runner = store, runner
        self._line = queue.Queue(maxsize=max_waiting)
        self._stop = False
        threading.Thread(target=self._work, name="court", daemon=True).start()

    def submit(self, hid: str) -> None:
        try:
            self._line.put_nowait(hid)
        except queue.Full:
            raise Busy from None

    def _work(self) -> None:
        while not self._stop:
            hid = self._line.get()
            if hid is not None:
                self._hear(hid)

    def _hear(self, hid: str) -> None:
        """One hearing; any error fails this hearing only, never the worker thread."""
        try:
            h = self.store.get(hid)
            if h is None:
                return
            self.store.start(hid)
            self.store.finish(hid, self.runner(h["text_a"], h["text_b"], h["seed"]))
        except Exception:
            log.exception("hearing %s failed", hid)
            try:
                self.store.fail(hid)
            except Exception:
                log.exception("could not mark hearing %s failed", hid)

    def close(self) -> None:
        """Stop after the current hearing; the rest stay queued and fail at next startup."""
        self._stop = True
        try:
            self._line.put_nowait(None)
        except queue.Full:
            pass
