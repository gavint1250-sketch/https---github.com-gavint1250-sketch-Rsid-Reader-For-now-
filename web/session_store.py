"""
Thread-safe in-memory session and job store.

Each browser tab creates one session (keyed by a UUID session_id generated
client-side and stored in sessionStorage).  Sessions are completely isolated —
a job can only be retrieved by supplying its exact session_id.

Sessions expire after SESSION_TTL seconds of inactivity.  purge_stale_sessions()
is called opportunistically on each upload request; it returns a list of temp
directories that the caller should delete (avoids temp files accumulating if the
browser beacon never fires).
"""

import threading
import time
import uuid

SESSION_TTL = 1800  # 30 minutes inactivity

_sessions: dict = {}
_lock = threading.Lock()


def ensure_session(session_id: str) -> None:
    """Create the session if it does not exist, and update last_seen."""
    with _lock:
        if session_id not in _sessions:
            _sessions[session_id] = {"last_seen": time.time(), "jobs": {}}
        else:
            _sessions[session_id]["last_seen"] = time.time()


def create_job(session_id: str) -> str:
    """Add a new pending job to the session; return its job_id."""
    job_id = str(uuid.uuid4())
    with _lock:
        if session_id not in _sessions:
            _sessions[session_id] = {"last_seen": time.time(), "jobs": {}}
        _sessions[session_id]["jobs"][job_id] = {
            "status": "pending",
            "progress_pct": 0,
            "progress_msg": "Waiting to start…",
            "findings": [],
            "report_html": None,
            "filenames": [],
            "error_msg": None,
            "temp_dir": None,
        }
    return job_id


def update_job(session_id: str, job_id: str, **kwargs) -> None:
    """Thread-safe update of any fields on an existing job."""
    with _lock:
        try:
            job = _sessions[session_id]["jobs"][job_id]
            job.update(kwargs)
        except KeyError:
            pass  # session or job may have been cleaned up already


def get_job(session_id: str, job_id: str) -> dict | None:
    """Return a shallow copy of the job dict, or None if not found."""
    with _lock:
        try:
            return dict(_sessions[session_id]["jobs"][job_id])
        except KeyError:
            return None


def delete_session(session_id: str) -> list[str]:
    """
    Remove the session from the store.

    Returns a list of temp_dir paths that the caller should delete with
    shutil.rmtree so that uploaded files are removed from disk.
    """
    with _lock:
        session = _sessions.pop(session_id, None)
    if session is None:
        return []
    dirs = []
    for job in session["jobs"].values():
        td = job.get("temp_dir")
        if td:
            dirs.append(td)
    return dirs


def purge_stale_sessions() -> list[str]:
    """
    Remove sessions that have been inactive for longer than SESSION_TTL.

    Returns a list of temp_dir paths that should be deleted by the caller.
    Called opportunistically at the start of each /upload request.
    """
    cutoff = time.time() - SESSION_TTL
    stale_ids = []
    with _lock:
        for sid, data in list(_sessions.items()):
            if data["last_seen"] < cutoff:
                stale_ids.append(sid)
        dirs = []
        for sid in stale_ids:
            session = _sessions.pop(sid, None)
            if session:
                for job in session["jobs"].values():
                    td = job.get("temp_dir")
                    if td:
                        dirs.append(td)
    return dirs
