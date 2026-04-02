"""
Background analysis worker.

run_analysis() is intended to be called from a daemon threading.Thread.
It calls the existing analysis modules (unchanged), writes progress updates
into the session store, and always cleans up the temp directory — even if
an exception is raised.
"""

import shutil

from web.session_store import update_job


def run_analysis(session_id: str, job_id: str,
                 file_paths: list, original_names: list, temp_dir: str) -> None:
    """
    Analyse one or more uploaded files and store results in the session store.

    Parameters
    ----------
    session_id    UUID that identifies the browser tab's session.
    job_id        UUID for this analysis job.
    file_paths    Absolute paths to the uploaded files in temp_dir.
    original_names  Original filenames as uploaded (for display only).
    temp_dir      Directory containing all uploaded files; deleted in finally.
    """
    # Import here so that the env-var / sys.path bootstrap in web_app.py has
    # already run before these heavyweight imports occur.
    from modules.file_analyzer import analyze_file
    from modules.report_generator import generate_html_report
    # generate_html_report(report_data, findings) — paragraphs first (line 108)

    try:
        update_job(session_id, job_id,
                   status="running", progress_pct=5,
                   progress_msg="Starting analysis…")

        all_findings: list = []
        all_report_data: list = []

        for i, (fpath, fname) in enumerate(zip(file_paths, original_names)):
            pct = 5 + int((i / len(file_paths)) * 85)
            update_job(session_id, job_id,
                       progress_pct=pct,
                       progress_msg=f"Analysing {fname}…")

            if len(file_paths) > 1:
                separator = "=" * 60
                all_findings += [separator, f"=== FILE: {fname} ===", separator]

            findings, report_data = analyze_file(fpath)
            all_findings.extend(findings)
            all_report_data.extend(report_data)

            if len(file_paths) > 1:
                all_findings.append("")  # blank line between files

        update_job(session_id, job_id,
                   progress_pct=95, progress_msg="Building report…")

        report_html = None
        if all_report_data:
            report_html = generate_html_report(all_report_data, all_findings)

        update_job(session_id, job_id,
                   status="done",
                   progress_pct=100,
                   progress_msg="Analysis complete.",
                   findings=all_findings,
                   report_html=report_html)

    except Exception as exc:
        update_job(session_id, job_id,
                   status="error",
                   error_msg=str(exc),
                   progress_msg="An error occurred during analysis.")

    finally:
        # Always delete uploaded files, regardless of success or failure.
        shutil.rmtree(temp_dir, ignore_errors=True)
