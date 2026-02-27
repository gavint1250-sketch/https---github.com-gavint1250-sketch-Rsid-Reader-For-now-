
def check_revision(props):
    """
    Reports the raw revision count from document core properties.

    Args:
        props: A python-docx CoreProperties object.

    Returns:
        list: A single-item list with the revision count, or empty if not set.
    """
    findings = []
    rev = props.revision
    if rev is not None:
        findings.append(f"[REVISION] Revision count: {rev}")
    return findings
