"""Arka plan iş kuyruğu. Her araç bir 'job' olarak thread içinde çalışır,
ilerleme bilgisi arayüze (JS) anlık olarak gönderilir."""
import json
import os
import threading
import time
import traceback
import uuid


class Cancelled(Exception):
    pass


class JobContext:
    def __init__(self, manager, job):
        self._m = manager
        self.job = job
        self.out_dir = job["out_dir"]
        self._cancel = threading.Event()

    # --- araçların kullandığı API ---
    @property
    def cancelled(self) -> bool:
        return self._cancel.is_set()

    def check(self):
        if self._cancel.is_set():
            raise Cancelled()

    def progress(self, fraction=None, message=None):
        self.check()
        if fraction is not None:
            self.job["progress"] = max(0.0, min(1.0, float(fraction)))
        if message is not None:
            self.job["message"] = message
        self._m._push(self.job)

    def add_output(self, path):
        self.job["outputs"].append(path)

    def out_path(self, filename):
        from .paths import unique_path
        os.makedirs(self.out_dir, exist_ok=True)
        return unique_path(os.path.join(self.out_dir, filename))


class JobManager:
    def __init__(self):
        self.jobs = {}
        self.contexts = {}
        self.listener = None          # fn(json_str) -> JS'e iletir
        self._last_push = {}
        self._lock = threading.Lock()

    def _push(self, job, force=False):
        now = time.time()
        if not force and now - self._last_push.get(job["id"], 0) < 0.15:
            return
        self._last_push[job["id"]] = now
        if self.listener:
            try:
                self.listener(json.dumps(self.public(job), ensure_ascii=False))
            except Exception:
                pass

    @staticmethod
    def public(job):
        return {k: v for k, v in job.items() if not k.startswith("_")}

    def start(self, tool, files, options, out_dir, title):
        job_id = uuid.uuid4().hex[:10]
        job = {
            "id": job_id, "tool": tool["id"], "tool_name": tool["name"], "icon": tool.get("icon", ""),
            "title": title, "status": "running", "progress": 0.0, "message": "Başlatılıyor...",
            "outputs": [], "out_dir": out_dir, "error": None,
            "started": time.time(), "finished": None,
        }
        ctx = JobContext(self, job)
        with self._lock:
            self.jobs[job_id] = job
            self.contexts[job_id] = ctx
        self._push(job, force=True)
        threading.Thread(target=self._run, args=(tool, files, options, ctx), daemon=True).start()
        return self.public(job)

    def _run(self, tool, files, options, ctx):
        job = ctx.job
        try:
            os.makedirs(ctx.out_dir, exist_ok=True)
            tool["handler"](ctx, files, options)
            job["status"] = "done"
            job["progress"] = 1.0
            n = len(job["outputs"])
            job["message"] = f"Tamamlandı! {n} dosya oluşturuldu." if n else "Tamamlandı!"
        except Cancelled:
            job["status"] = "cancelled"
            job["message"] = "İşlem iptal edildi."
        except Exception as e:
            traceback.print_exc()
            job["status"] = "error"
            job["error"] = str(e)
            job["message"] = f"Hata: {e}"
        finally:
            job["finished"] = time.time()
            self._push(job, force=True)

    def cancel(self, job_id):
        ctx = self.contexts.get(job_id)
        if ctx:
            ctx._cancel.set()
            proc = ctx.job.get("_proc")
            if proc is not None:
                try:
                    proc.kill()
                except Exception:
                    pass
        return True

    def list(self):
        return [self.public(j) for j in sorted(self.jobs.values(), key=lambda j: j["started"], reverse=True)]

    def clear_finished(self):
        with self._lock:
            for jid in [j for j, v in self.jobs.items() if v["status"] != "running"]:
                self.jobs.pop(jid, None)
                self.contexts.pop(jid, None)
        return self.list()
