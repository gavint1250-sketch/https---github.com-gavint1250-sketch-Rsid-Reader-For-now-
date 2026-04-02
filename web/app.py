"""
Flask application factory and all routes.

Routes
------
GET  /                          Serve the single-page UI
POST /upload                    Accept files, start background analysis job
GET  /status/<sid>/<jid>        Poll job progress
GET  /report/<sid>/<jid>        Return self-contained HTML report
GET  /download_txt/<sid>/<jid>  Download findings as plain-text attachment
POST /session/cleanup           Delete session data (called by sendBeacon on exit)
"""

import io
import os
import shutil
import tempfile
import threading
import zipfile

from flask import Flask, jsonify, render_template, request, send_file

from web.analysis_worker import run_analysis
from web.session_store import (
    create_job,
    delete_session,
    ensure_session,
    get_job,
    purge_stale_sessions,
    update_job,
)

ALLOWED_EXTENSIONS = {".docx", ".pdf", ".xml", ".zip"}
MAX_UPLOAD_BYTES = 200 * 1024 * 1024  # 200 MB


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates")
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

    # ------------------------------------------------------------------
    # Main page
    # ------------------------------------------------------------------

    @app.get("/")
    def index():
        return render_template("index.html")

    # ------------------------------------------------------------------
    # Upload endpoint
    # ------------------------------------------------------------------

    @app.post("/upload")
    def upload():
        # Opportunistically clean up stale sessions and their temp files.
        for stale_dir in purge_stale_sessions():
            shutil.rmtree(stale_dir, ignore_errors=True)

        session_id = request.form.get("session_id", "").strip()
        if not session_id:
            return jsonify({"error": "Missing session_id."}), 400
        ensure_session(session_id)

        uploaded = request.files.getlist("files")
        if not uploaded or all(f.filename == "" for f in uploaded):
            return jsonify({"error": "No files received."}), 400

        # Validate extensions before touching the filesystem.
        for f in uploaded:
            ext = os.path.splitext(f.filename)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                return jsonify({
                    "error": (
                        f"Unsupported file type: {f.filename}. "
                        "Please upload .docx, .pdf, .xml, or a .zip archive."
                    )
                }), 400

        # Save all files to an isolated temp directory for this job.
        temp_dir = tempfile.mkdtemp()
        try:
            file_paths: list[str] = []
            original_names: list[str] = []

            for f in uploaded:
                ext = os.path.splitext(f.filename)[1].lower()
                dest = os.path.join(temp_dir, f.filename)
                f.save(dest)

                if ext == ".zip":
                    # Extract .docx / .pdf files from the archive.
                    extracted = _safe_extract_zip(dest, temp_dir)
                    file_paths.extend(extracted["paths"])
                    original_names.extend(extracted["names"])
                    os.remove(dest)  # remove the zip itself
                else:
                    file_paths.append(dest)
                    original_names.append(f.filename)

            if not file_paths:
                shutil.rmtree(temp_dir, ignore_errors=True)
                return jsonify({
                    "error": (
                        "The uploaded ZIP contained no supported files "
                        "(.docx, .pdf, .xml)."
                    )
                }), 400

        except Exception as exc:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return jsonify({"error": f"File processing error: {exc}"}), 500

        job_id = create_job(session_id)
        # Store temp_dir on the job so cleanup can find it even if the worker
        # hasn't started yet (e.g. if TTL expires before the thread fires).
        update_job(session_id, job_id,
                   temp_dir=temp_dir, filenames=original_names)

        thread = threading.Thread(
            target=run_analysis,
            args=(session_id, job_id, file_paths, original_names, temp_dir),
            daemon=True,
        )
        thread.start()

        return jsonify({"job_id": job_id}), 202

    # ------------------------------------------------------------------
    # Status polling
    # ------------------------------------------------------------------

    @app.get("/status/<session_id>/<job_id>")
    def status(session_id: str, job_id: str):
        ensure_session(session_id)
        job = get_job(session_id, job_id)
        if job is None:
            return jsonify({"error": "Job not found."}), 404

        payload: dict = {
            "status": job["status"],
            "progress_pct": job["progress_pct"],
            "progress_msg": job["progress_msg"],
        }
        if job["status"] == "done":
            payload["findings"] = job["findings"]
            payload["has_report"] = bool(job.get("report_html"))
        elif job["status"] == "error":
            payload["error_msg"] = job.get("error_msg") or "Unknown error."

        return jsonify(payload)

    # ------------------------------------------------------------------
    # HTML report download (opens in new tab)
    # ------------------------------------------------------------------

    @app.get("/report/<session_id>/<job_id>")
    def report(session_id: str, job_id: str):
        job = get_job(session_id, job_id)
        if job is None or job.get("report_html") is None:
            return jsonify({"error": "Report not found."}), 404
        return job["report_html"], 200, {"Content-Type": "text/html; charset=utf-8"}

    # ------------------------------------------------------------------
    # Plain-text findings download
    # ------------------------------------------------------------------

    @app.get("/download_txt/<session_id>/<job_id>")
    def download_txt(session_id: str, job_id: str):
        job = get_job(session_id, job_id)
        if job is None or job["status"] != "done":
            return jsonify({"error": "Results not available."}), 404

        text = "\n".join(job["findings"])
        buf = io.BytesIO(text.encode("utf-8"))
        buf.seek(0)
        return send_file(
            buf,
            mimetype="text/plain",
            as_attachment=True,
            download_name="analysis_results.txt",
        )

    # ------------------------------------------------------------------
    # Session cleanup (called by navigator.sendBeacon on page exit)
    # ------------------------------------------------------------------

    @app.post("/session/cleanup")
    def session_cleanup():
        data = request.get_json(silent=True) or {}
        session_id = data.get("session_id", "").strip()
        if session_id:
            temp_dirs = delete_session(session_id)
            for td in temp_dirs:
                shutil.rmtree(td, ignore_errors=True)
        return "", 204

    # ------------------------------------------------------------------
    # Error handlers
    # ------------------------------------------------------------------

    @app.errorhandler(413)
    def too_large(_e):
        return jsonify({"error": "File too large. Maximum upload size is 200 MB."}), 413

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"error": "Not found."}), 404

    return app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_extract_zip(zip_path: str, dest_dir: str) -> dict:
    """
    Extract .docx / .pdf / .xml members from a ZIP archive.

    Guards against zip-slip (path-traversal) attacks by verifying that every
    extracted path resolves inside dest_dir.

    Returns {"paths": [...], "names": [...]} for extracted files.
    """
    real_dest = os.path.realpath(dest_dir)
    paths: list[str] = []
    names: list[str] = []

    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            # Skip directories and unsupported file types.
            if member.is_dir():
                continue
            ext = os.path.splitext(member.filename)[1].lower()
            if ext not in {".docx", ".pdf", ".xml"}:
                continue

            # Use only the basename to flatten the archive's directory structure
            # and prevent path traversal via nested "../" components.
            safe_name = os.path.basename(member.filename)
            if not safe_name:
                continue

            target = os.path.realpath(os.path.join(dest_dir, safe_name))
            if not target.startswith(real_dest + os.sep):
                continue  # zip-slip attempt — skip silently

            # Extract to safe_name (not member.filename) to avoid nested dirs.
            with zf.open(member) as src, open(target, "wb") as dst:
                dst.write(src.read())

            paths.append(target)
            names.append(safe_name)

    return {"paths": paths, "names": names}
