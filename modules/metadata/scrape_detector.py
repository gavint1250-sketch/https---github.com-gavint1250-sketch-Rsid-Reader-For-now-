
import zipfile
from datetime import timezone


def check_scrape_indicators(file_path, props):
    """
    Checks for patterns that suggest document metadata has been deliberately removed.

    Looks for three distinct signals:
      1. docProps/core.xml missing entirely from the ZIP
      2. Multiple key fields blank simultaneously
      3. 'created' and 'last_modified' timestamps being identical (common metadata-reset artifact)

    Args:
        file_path (str): The path to the .docx file (needed to inspect the ZIP structure).
        props:          A python-docx CoreProperties object.

    Returns:
        list: Finding strings describing any scrape indicators detected.
    """
    findings = []

    # --- Check 1: Is docProps/core.xml present at all? ---
    try:
        with zipfile.ZipFile(file_path, 'r') as z:
            core_present = 'docProps/core.xml' in z.namelist()
    except zipfile.BadZipFile:
        findings.append("[SCRAPE] Could not inspect ZIP structure — file may be corrupted.")
        return findings
    except Exception as e:
        findings.append(f"[SCRAPE] Error inspecting file structure: {e}")
        return findings

    if not core_present:
        findings.append(
            "[SCRAPE] docProps/core.xml is absent from the file. "
            "The core metadata file has been removed entirely."
        )
        return findings

    # --- Check 2: Multiple key fields blank simultaneously ---
    key_fields = {
        "author":           props.author,
        "created":          props.created,
        "last_modified":    props.modified,
        "last_modified_by": props.last_modified_by,
    }

    blank = [
        name for name, val in key_fields.items()
        if val is None or (isinstance(val, str) and not val.strip())
    ]

    if len(blank) >= 3:
        findings.append(
            f"[SCRAPE] {len(blank)}/4 key metadata fields are blank or absent "
            f"({', '.join(blank)})."
        )
    elif len(blank) == 2:
        findings.append(
            f"[SCRAPE] 2/4 key metadata fields are blank or absent "
            f"({', '.join(blank)})."
        )

    # --- Check 3: created == last_modified (metadata reset artifact) ---
    created  = props.created
    modified = props.modified

    if created is not None and modified is not None:
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        if modified.tzinfo is None:
            modified = modified.replace(tzinfo=timezone.utc)

        if created == modified:
            findings.append(
                "[SCRAPE] 'created' and 'last_modified' timestamps are identical. "
                "This can occur when metadata is reset by a removal tool."
            )

    return findings
