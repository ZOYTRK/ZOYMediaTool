"""JavaScript tarafına açılan API (window.pywebview.api.*)."""
import os
import subprocess
import webbrowser

import webview

from . import settings
from .catalog import TOOLS, TOOL_MAP, C
from .jobs import JobManager
from .paths import find_ffmpeg, find_soffice, find_tesseract

DEPS = {
    "ffmpeg": ("FFmpeg Medya Motoru", find_ffmpeg, "https://www.gyan.dev/ffmpeg/builds/"),
}


class Api:
    def __init__(self):
        self._window = None
        self._jobs = JobManager()

    # ---------- yardımcılar ----------
    @staticmethod
    def _dep_status():
        out = {}
        for key, (name, finder, url) in DEPS.items():
            path = finder()
            out[key] = {"name": name, "ok": bool(path), "path": path or "", "url": url}
        return out

    @staticmethod
    def _file_info(path):
        try:
            size = os.path.getsize(path) if os.path.isfile(path) else 0
        except OSError:
            size = 0
        return {"path": path, "name": os.path.basename(path), "size": size,
                "ext": os.path.splitext(path)[1].lower().lstrip(".")}

    # ---------- başlangıç ----------
    def get_bootstrap(self):
        deps = self._dep_status()
        tools = []
        for t in TOOLS:
            missing = [DEPS[r][0] for r in t.get("requires", []) if r in deps and not deps[r]["ok"]]
            pub = {k: v for k, v in t.items() if k != "handler"}
            pub["implemented"] = t["handler"] is not None
            pub["missing"] = missing
            tools.append(pub)
        try:
            import yt_dlp
            ytv = yt_dlp.version.__version__
        except Exception:
            ytv = "?"
        return {
            "settings": settings.load(),
            "tools": tools,
            "categories": [{"id": k, "name": v[0], "group": v[1], "icon": v[2]} for k, v in C.items()],
            "deps": deps,
            "versions": {"yt_dlp": ytv},
            "jobs": self._jobs.list(),
        }

    # ---------- dosya seçimi ----------
    def pick_files(self, tool_id):
        t = TOOL_MAP.get(tool_id, {})
        types = ["Tüm dosyalar (*.*)"]
        if t.get("accept"):
            pattern = ";".join(f"*.{e}" for e in t["accept"])
            types.insert(0, f"Desteklenen dosyalar ({pattern})")
        res = self._window.create_file_dialog(webview.FileDialog.OPEN, allow_multiple=t.get("multiple", True),
                                              file_types=tuple(types))
        return [self._file_info(p) for p in (res or [])]

    def pick_folder(self):
        res = self._window.create_file_dialog(webview.FileDialog.FOLDER)
        return res[0] if res else None

    def file_info(self, paths):
        return [self._file_info(p) for p in paths if p and os.path.exists(p)]

    # ---------- işler ----------
    def run_tool(self, tool_id, inputs, options):
        t = TOOL_MAP.get(tool_id)
        if not t:
            return {"error": "Araç bulunamadı."}
        if not t["handler"]:
            return {"error": "Bu araç henüz eklenmedi (yakında)."}
        deps = self._dep_status()
        missing = [DEPS[r][0] for r in t.get("requires", []) if r in deps and not deps[r]["ok"]]
        if missing:
            return {"error": f"Gerekli program eksik: {', '.join(missing)}"}
        inputs = [i for i in (inputs or []) if i]
        if len(inputs) < t["min_files"]:
            need = "URL" if t["input"] == "url" else "dosya"
            return {"error": f"En az {t['min_files']} {need} gerekli."}
        out_dir = settings.load()["output_dir"]
        if t["input"] == "url":
            title = inputs[0] if len(inputs) == 1 else f"{len(inputs)} bağlantı"
        else:
            title = os.path.basename(inputs[0]) if len(inputs) == 1 else f"{len(inputs)} dosya"
        return self._jobs.start(t, inputs, options or {}, out_dir, title)

    def cancel_job(self, job_id):
        return self._jobs.cancel(job_id)

    def list_jobs(self):
        return self._jobs.list()

    def clear_jobs(self):
        return self._jobs.clear_finished()

    # ---------- sistem ----------
    def open_path(self, path):
        if path and os.path.exists(path):
            os.startfile(path)
            return True
        return False

    def reveal_path(self, path):
        if path and os.path.exists(path):
            subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
            return True
        return False

    def open_output_dir(self):
        d = settings.load()["output_dir"]
        os.makedirs(d, exist_ok=True)
        os.startfile(d)
        return True

    def open_url(self, url):
        webbrowser.open(url)
        return True

    def save_settings(self, values):
        return settings.save(values or {})

    def refresh_deps(self):
        return self._dep_status()
