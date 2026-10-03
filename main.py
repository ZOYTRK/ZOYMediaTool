"""ZOY Media Tool — Windows XP temalı medya, dönüştürme ve PDF araç kutusu.
Arayüz: web/ (HTML/CSS/JS)  |  Arka uç: app/ (Python)"""
import json
import sys

import webview
from webview.dom import DOMEventHandler

from app.api import Api
from app.paths import resource_path


def main():
    api = Api()
    window = webview.create_window(
        "ZOY Media Tool",
        url=resource_path("web/index.html"),
        js_api=api,
        width=1320, height=840, min_size=(1024, 660),
        background_color="#1c2333",
    )
    api._window = window

    def push_js(code):
        runner = getattr(window, "run_js", None) or window.evaluate_js
        try:
            runner(code)
        except Exception:
            pass

    api._jobs.listener = lambda payload: push_js(f"window.onJobUpdate && window.onJobUpdate({payload})")

    def on_drop(e):
        files = (e.get("dataTransfer") or {}).get("files") or []
        paths = [f.get("pywebviewFullPath") for f in files if f.get("pywebviewFullPath")]
        if paths:
            push_js(f"window.onFilesDropped && window.onFilesDropped({json.dumps(api.file_info(paths))})")

    def on_loaded():
        try:
            window.dom.document.events.dragover += DOMEventHandler(lambda e: None, True, True)
            window.dom.document.events.drop += DOMEventHandler(on_drop, True, True)
        except Exception as ex:
            print("Sürükle-bırak bağlanamadı:", ex)

    window.events.loaded += on_loaded
    webview.start(debug="--debug" in sys.argv, icon=resource_path("logo.ico"))


if __name__ == "__main__":
    main()