"""Chụp bản thử mobile bằng Playwright: viewport thật 390x844, cả sáng và tối."""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parent
URL = (BASE / "prototype_app.html").as_uri()
SHOTS = BASE / "shots"
SHOTS.mkdir(exist_ok=True)

SCREENS = ["home", "work", "detail", "people", "form", "more", "me"]


def report_overflow(page, label):
    data = page.evaluate(
        """() => {
            const vw = document.documentElement.clientWidth;
            const bad = [];
            document.querySelectorAll('body *').forEach(el => {
                const r = el.getBoundingClientRect();
                if (r.width > 0 && (r.right > vw + 1 || r.left < -1)) {
                    bad.push({ tag: el.tagName.toLowerCase(), cls: (el.className || '').toString().slice(0, 60) });
                }
            });
            return { vw, scrollW: document.documentElement.scrollWidth, bad: bad.slice(0, 8) };
        }"""
    )
    flag = "OK" if data["scrollW"] <= data["vw"] else "OVERFLOW"
    print(f"[{label}] viewport={data['vw']} scrollWidth={data['scrollW']} {flag}")
    for b in data["bad"]:
        print(f"   -> <{b['tag']} class='{b['cls']}'>")


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)

        for theme in ("light", "dark"):
            for screen in SCREENS:
                page.goto(f"{URL}?s={screen}&theme={theme}", wait_until="load")
                page.wait_for_timeout(320)
                report_overflow(page, f"{screen}/{theme}")
                suffix = "" if theme == "light" else "_dark"
                page.screenshot(path=str(SHOTS / f"{screen}{suffix}.png"))

        for theme in ("light", "dark"):
            page.goto(f"{URL}?s=work&theme={theme}", wait_until="load")
            page.wait_for_timeout(250)
            page.click('[data-sheet="filter"]')
            page.wait_for_timeout(480)
            suffix = "" if theme == "light" else "_dark"
            page.screenshot(path=str(SHOTS / f"sheet{suffix}.png"))

        browser.close()
        print("done")


if __name__ == "__main__":
    sys.exit(main())
