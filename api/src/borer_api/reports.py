"""Reports, the admin's moderation steps and the "send the verdict" mark on the case store
(SPEC §10, §15.5).

One report hides the whole case at once (`hidden_at`): its public card and both personal
pages answer "case closed". The admin lists reported or hidden cases, restores one
(visible again; its reports stay on record) or deletes one with everything in it.
"""


class Reports:
    """Mixed into cases.Store (uses its connection helpers and clock)."""

    def report(self, cid: str) -> bool:
        """Record a report and hide the case; False if it is gone or already hidden."""
        with self._tx():
            if self._one('SELECT id FROM "case" WHERE id = ? AND created_at >= ? '
                         "AND hidden_at IS NULL", (cid, self.oldest_kept())) is None:
                return False
            self._run("INSERT INTO report (case_id, created_at) VALUES (?, ?)", (cid, self.clock()))
            self._run('UPDATE "case" SET hidden_at = ? WHERE id = ?', (self.clock(), cid))
            self.bump("reports")
            return True

    def shared(self, cid: str) -> bool:
        """A "send the verdict" tap: the first one sets shared_at and counts the case once,
        in cases_shared (both sides wrote) or no_shows_shared; later taps (either side, any
        device) change nothing."""
        with self._tx():
            if self._run('UPDATE "case" SET shared_at = ? WHERE id = ? AND shared_at IS NULL',
                         (self.clock(), cid)) != 1:
                return False
            no_show = self._one('SELECT text_b IS NULL AS n FROM "case" WHERE id = ?', (cid,))["n"]
            self.bump("no_shows_shared" if no_show else "cases_shared")
            return True

    def reported(self) -> list[dict]:
        """Cases that were reported or are hidden, oldest first, with their report count."""
        return self._all('SELECT c.*, COUNT(r.id) AS reports FROM "case" c '
                         "LEFT JOIN report r ON r.case_id = c.id GROUP BY c.id "
                         "HAVING c.hidden_at IS NOT NULL OR COUNT(r.id) > 0 ORDER BY c.created_at")

    def restore(self, cid: str) -> bool:
        return self._run('UPDATE "case" SET hidden_at = NULL WHERE id = ? '
                         "AND hidden_at IS NOT NULL", (cid,)) == 1

    def delete(self, cid: str) -> bool:
        """Delete a case with its hearings and reports."""
        return self._run('DELETE FROM "case" WHERE id = ?', (cid,)) == 1
