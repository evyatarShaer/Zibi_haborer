"""A minimal Chrome DevTools Protocol driver for the page tests (test_e2e_*.py).

Chrome is the Windows install, started headless from WSL (mirrored networking: both sides
share localhost). Each Page is its own browser context (own cookies and storage), i.e. its
own device, at 360 px. Chrome is closed over CDP: never taskkill, which would close the
owner's own windows.
"""
import json
import subprocess
import time
import urllib.request
from pathlib import Path

from websockets.sync.client import connect

CHROME = Path("/mnt/c/Program Files/Google/Chrome/Application/chrome.exe")


def windows_temp() -> str:
    out = subprocess.run(["cmd.exe", "/c", "echo %TEMP%"], capture_output=True, text=True)
    return out.stdout.strip()


class Browser:
    def __init__(self, port: int = 9333):
        profile = f"{windows_temp()}\\borer-e2e-{int(time.time())}"
        self.proc = subprocess.Popen(
            [str(CHROME), "--headless=new", f"--remote-debugging-port={port}", "--no-first-run",
             "--no-default-browser-check", f"--user-data-dir={profile}", "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        url = f"http://127.0.0.1:{port}/json/version"
        for _ in range(100):
            try:
                ws = json.load(urllib.request.urlopen(url, timeout=1))["webSocketDebuggerUrl"]
                break
            except OSError:
                time.sleep(0.2)
        else:
            raise RuntimeError("Chrome did not start")
        self.ws, self.n, self.errors = connect(ws, max_size=None, close_timeout=1).__enter__(), 0, []

    def send(self, method: str, session: str | None = None, **params):
        self.n += 1
        msg = {"id": self.n, "method": method, "params": params}
        if session:
            msg["sessionId"] = session
        self.ws.send(json.dumps(msg))
        while True:
            m = json.loads(self.ws.recv(timeout=30))
            if m.get("id") == self.n:
                if "error" in m:
                    raise RuntimeError(f"{method}: {m['error']}")
                return m["result"]
            if m.get("method") == "Runtime.exceptionThrown":  # a script error on any page
                self.errors.append(m["params"]["exceptionDetails"])

    def page(self) -> "Page":
        return Page(self)

    def close(self) -> None:
        try:
            self.send("Browser.close")
        except Exception:  # noqa: BLE001 - Chrome drops the socket as it closes
            pass
        self.proc.wait(timeout=10)


class Page:
    """One device: a fresh browser context with one tab, 360 × 740 CSS px, touch."""

    def __init__(self, browser: Browser):
        self.b = browser
        ctx = browser.send("Target.createBrowserContext")["browserContextId"]
        target = browser.send("Target.createTarget", url="about:blank", browserContextId=ctx)
        self.s = browser.send("Target.attachToTarget", targetId=target["targetId"], flatten=True)["sessionId"]
        for method in ("Page.enable", "Runtime.enable"):
            browser.send(method, self.s)
        browser.send("Emulation.setDeviceMetricsOverride", self.s, width=360, height=740,
                     deviceScaleFactor=2, mobile=True)

    def js(self, expr: str):
        r = self.b.send("Runtime.evaluate", self.s, expression=expr, returnByValue=True, awaitPromise=True)
        if "exceptionDetails" in r:
            raise RuntimeError(f"{expr}: {r['exceptionDetails']}")
        return r["result"].get("value")

    def wait(self, expr: str, timeout: float = 30):
        end = time.time() + timeout
        while time.time() < end:
            v = self.js(expr)
            if v:
                return v
            time.sleep(0.1)
        raise AssertionError(f"timed out: {expr}\n--- {self.js('location.href')} "
                             f"{self.js('document.readyState')} ---\n{self.text()}")

    def goto(self, url: str) -> None:
        self.b.send("Page.navigate", self.s, url=url)
        time.sleep(0.2)
        if url.startswith("http"):  # one of our pages: wait until its script has drawn
            self.wait("document.readyState === 'complete' && document.getElementById('app')"
                      " && document.getElementById('app').children.length > 0")

    def text(self) -> str:
        return self.js("document.body ? document.body.innerText : ''")

    def wait_text(self, s: str, timeout: float = 30) -> None:
        self.wait(f"document.body.innerText.includes({json.dumps(s)})", timeout)

    def fill(self, name: str, value: str) -> None:
        self.js(f"(() => {{ const e = document.querySelector('[name={name}]'); e.value = {json.dumps(value)};"
                " e.dispatchEvent(new Event('input', {bubbles: true})); })()")

    def click(self, selector: str) -> None:
        self.js(f"document.querySelector({json.dumps(selector)}).click()")

    def attr(self, selector: str, name: str):
        return self.js(f"(() => {{ const e = document.querySelector({json.dumps(selector)});"
                       f" return e && !e.hidden ? e.getAttribute({json.dumps(name)}) : null; }})()")

    def fits(self) -> bool:
        """No horizontal overflow at this width."""
        return self.js("document.documentElement.scrollWidth <= window.innerWidth")

    def path(self) -> str:
        return self.js("location.pathname")
