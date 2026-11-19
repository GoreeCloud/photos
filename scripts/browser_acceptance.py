import argparse
import asyncio
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import websockets

FIRST = "synthetic-browser-initial-2026"
SECOND = "synthetic-browser-rotated-2026"


class Chrome:
    def __init__(self, socket):
        self.socket = socket
        self.counter = 0

    async def run(self, method, params=None):
        self.counter += 1
        index = self.counter
        await self.socket.send(
            json.dumps({"id": index, "method": method, "params": params or {}})
        )
        while True:
            packet = json.loads(await asyncio.wait_for(self.socket.recv(), timeout=20))
            if packet.get("id") == index:
                if "error" in packet:
                    raise RuntimeError(str(packet["error"]))
                return packet.get("result", {})

    async def js(self, expression):
        response = await self.run(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
        )
        if "exceptionDetails" in response:
            raise AssertionError(
                "Chrome JS failed: " + str(response["exceptionDetails"].get("text"))
            )
        return response.get("result", {}).get("value")

    async def wait(self, expression, label):
        for _ in range(80):
            try:
                matches = await self.js(expression)
            except (TimeoutError, AssertionError, RuntimeError):
                matches = False
            if matches:
                return
            await asyncio.sleep(0.17)
        raise AssertionError("Timed out: " + label)

    async def fill(self, selector, value):
        js = """(() => {
            const e = document.querySelector(SELECTOR);
            if (!e) return false;
            const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
            set.call(e, VALUE);
            e.dispatchEvent(new Event('input',{bubbles:true}));
            return e.value === VALUE;
        })()"""
        js = js.replace("SELECTOR", json.dumps(selector)).replace(
            "VALUE", json.dumps(value)
        )
        assert await self.js(js), "Input unavailable: " + selector

    async def click(self, label):
        js = """(() => {
            const b = [...document.querySelectorAll('button')].find(x=>x.textContent.trim()===LABEL);
            if (!b || b.disabled) return false;
            b.click(); return true;
        })()""".replace("LABEL", json.dumps(label))
        assert await self.js(js), "Button missing or disabled: " + label

    async def escape(self):
        for kind in ("keyDown", "keyUp"):
            await self.run(
                "Input.dispatchKeyEvent",
                {
                    "type": kind,
                    "key": "Escape",
                    "code": "Escape",
                    "windowsVirtualKeyCode": 27,
                },
            )


async def check_browser(app_url: str, cdp_url: str):
    def read_tabs():
        with urllib.request.urlopen(cdp_url + "/json/list", timeout=3) as response:
            return json.load(response)

    tabs = await asyncio.to_thread(read_tabs)
    url = next(x["webSocketDebuggerUrl"] for x in tabs if x["type"] == "page")
    async with websockets.connect(url, max_size=4 * 1024 * 1024) as socket:
        browser = Chrome(socket)
        await browser.run("Page.enable")
        await browser.run("Runtime.enable")
        await browser.run("Page.navigate", {"url": app_url})
        await browser.wait(
            'Boolean(document.querySelector("input#password"))', "initial login"
        )
        await browser.fill("#password", FIRST)
        await browser.click("Unlock library")
        await browser.wait(
            'document.body.innerText.includes("browser-synthetic-only.png")',
            "synthetic gallery",
        )
        assert await browser.js(
            'document.querySelectorAll(".timeline-day").length===1'
        )
        assert await browser.js(
            'document.querySelector(".timeline-heading h3")?.textContent?.startsWith("Imported ")'
        )
        assert await browser.js(
            'document.querySelector("details.library-metrics")?.open===false'
        )
        assert await browser.js(
            '(() => { const info=document.querySelector("details.library-metrics");'
            ' info.querySelector("summary").click(); return info.open; })()'
        )
        print("PASS: UTC import timeline and accessible library details disclosure", flush=True)
        print("PASS: Chromium login and synthetic gallery", flush=True)
        await browser.click("Security")
        await browser.wait(
            'document.activeElement?.id==="photos-current-secret"', "security autofocus"
        )
        assert await browser.js(
            'Array.from(document.querySelectorAll("#library-security-settings input")).every(x=>x.type==="password")'
        )
        print("PASS: masked fields and keyboard focus", flush=True)
        await browser.fill("#photos-current-secret", "bad-test-credential")
        await browser.fill("#photos-new-secret", SECOND)
        await browser.fill("#photos-confirm-secret", SECOND)
        await browser.click("Change password and revoke sessions")
        await browser.wait(
            'document.body.innerText.includes("Invalid current password")',
            "error response",
        )
        assert await browser.js(
            'Boolean(document.querySelector("#library-security-settings [role=alert]"))'
        )
        print("PASS: accessible failed password response", flush=True)
        await browser.fill("#photos-current-secret", FIRST)
        await browser.click("Change password and revoke sessions")
        await browser.wait(
            'document.body.innerText.includes("Password changed. All sessions were revoked")',
            "password rotation",
        )
        assert await browser.js('Boolean(document.querySelector("input#password"))')
        assert not await browser.js(
            'document.body.innerText.includes("browser-synthetic-only.png")'
        )
        print("PASS: password rotation clears private browser session", flush=True)
        await browser.fill("#password", SECOND)
        await browser.click("Unlock library")
        await browser.wait(
            'document.body.innerText.includes("browser-synthetic-only.png")',
            "relogin with new password",
        )
        await browser.click("Security")
        await browser.wait(
            'document.activeElement?.id==="photos-current-secret"', "reopened settings"
        )
        await browser.fill("#photos-current-secret", SECOND)
        await browser.click("Sign out all devices without changing password")
        await browser.wait(
            'document.body.innerText.includes("All devices signed out")',
            "global revocation",
        )
        assert await browser.js('Boolean(document.querySelector("input#password"))')
        print(
            "PASS: all-device sign-out clears UI without changing password", flush=True
        )
        await browser.fill("#password", SECOND)
        await browser.click("Unlock library")
        await browser.wait(
            'document.body.innerText.includes("browser-synthetic-only.png")',
            "relogin after revoke",
        )
        await browser.click("Security")
        await browser.wait(
            'document.activeElement?.id==="photos-current-secret"', "security panel"
        )
        await browser.fill("#photos-current-secret", "synthetic-draft")
        await browser.escape()
        await browser.wait(
            '!document.querySelector("#library-security-settings")', "Escape dismissal"
        )
        await browser.click("Security")
        await browser.wait(
            'Boolean(document.querySelector("#photos-current-secret"))',
            "settings reopen",
        )
        assert await browser.js(
            'document.querySelector("#photos-current-secret").value===""'
        )
        print("PASS: Escape closes settings and clears secret draft", flush=True)


def unused_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def wait_for_service(url: str, process: subprocess.Popen, description: str) -> None:
    for _ in range(60):
        if process.poll() is not None:
            raise RuntimeError(description + " exited during initialization")
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except (OSError, TimeoutError):
            pass
        time.sleep(0.2)
    raise RuntimeError(description + " did not initialize")


def stop_owned_process(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=3)


def run():
    parser = argparse.ArgumentParser(
        description="Disposable GoreeCloud Photos Chromium acceptance"
    )
    parser.add_argument(
        "--chromium",
        required=True,
        type=Path,
        help="Local Chromium/Chrome headless binary; never a remote browser",
    )
    parser.add_argument(
        "--unsafe-no-sandbox",
        action="store_true",
        help="Use only in a disposable trusted development environment",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if not args.chromium.is_file():
        parser.error("Chromium executable not found")
    if not (root / "web" / "dist" / "index.html").is_file():
        parser.error("Build web first with npm --prefix web run build")
    with tempfile.TemporaryDirectory(prefix="photos-browser-accept-") as directory:
        temp = Path(directory)
        os.chmod(temp, 0o700)
        api_port = unused_loopback_port()
        cdp_port = unused_loopback_port()
        while cdp_port == api_port:
            cdp_port = unused_loopback_port()
        env = {
            key: value
            for key, value in os.environ.items()
            if key
            in {
                "PATH",
                "HOME",
                "LANG",
                "LC_ALL",
                "LD_LIBRARY_PATH",
                "XDG_RUNTIME_DIR",
                "TMPDIR",
            }
        }
        env["PHOTOS_BROWSER_TEST_DIR"] = str(temp)
        env["PYTHONPATH"] = os.pathsep.join([str(root / "scripts"), str(root / "api")])
        api_process = None
        browser_process = None
        with (
            (temp / "api.log").open("wb") as api_log,
            (temp / "chromium.log").open("wb") as browser_log,
        ):
            try:
                api_process = subprocess.Popen(
                    [
                        sys.executable,
                        "-m",
                        "uvicorn",
                        "browser_fixture:app",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(api_port),
                    ],
                    cwd=root / "api",
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=api_log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                app_url = f"http://127.0.0.1:{api_port}/"
                cdp_url = f"http://127.0.0.1:{cdp_port}"
                wait_for_service(app_url + "health", api_process, "Synthetic API")
                flags = [
                    str(args.chromium),
                    "--headless",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--disable-extensions",
                    "--disable-background-networking",
                    "--disable-sync",
                    "--no-proxy-server",
                    "--no-first-run",
                    "--remote-debugging-address=127.0.0.1",
                    f"--remote-debugging-port={cdp_port}",
                    f"--user-data-dir={temp / 'chromium-profile'}",
                    "about:blank",
                ]
                if args.unsafe_no_sandbox:
                    flags.insert(1, "--no-sandbox")
                browser_process = subprocess.Popen(
                    flags,
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=browser_log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                wait_for_service(
                    cdp_url + "/json/version", browser_process, "Disposable Chromium"
                )
                asyncio.run(check_browser(app_url, cdp_url))
                print("PASS: full synthetic Chromium acceptance suite", flush=True)
            finally:
                stop_owned_process(browser_process)
                stop_owned_process(api_process)
                print("Cleaned up synthetic library and browser processes", flush=True)


if __name__ == "__main__":
    run()
