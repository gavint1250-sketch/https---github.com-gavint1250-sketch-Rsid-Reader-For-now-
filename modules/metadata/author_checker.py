
GENERIC_AUTHORS = {"user", "unknown", "author", "admin", "default"}


def check_author(props):
    """
    Reports blank or generic author field values as raw facts.

    Args:
        props: A python-docx CoreProperties object.

    Returns:
        list: A finding string if the author field is blank or generic, else empty list.
    """
    findings = []
    author = props.author

    if not author or not author.strip():
        findings.append("[AUTHOR] Author field is blank.")
    elif author.strip().lower() in GENERIC_AUTHORS:
        findings.append(f"[AUTHOR] Author field value: '{author}'")

    return findings
