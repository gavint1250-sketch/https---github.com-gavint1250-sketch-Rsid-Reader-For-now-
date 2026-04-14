from datetime import timezone


def check_timestamps(props):
    """
    Reports the document's creation and last-modification timestamps,
    and the time elapsed between them.

    Args:
        props: A python-docx CoreProperties object.

    Returns:
        list: Finding strings with raw timestamp data and calculated delta.
    """
    findings = []
    created  = props.created
    modified = props.modified

    if created is None and modified is None:
        return findings

    def _normalize(dt):
        if dt is not None and dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    created  = _normalize(created)
    modified = _normalize(modified)

    if created is not None:
        findings.append(f"[TIMESTAMP] Created:       {created.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    if modified is not None:
        findings.append(f"[TIMESTAMP] Last Modified: {modified.strftime('%Y-%m-%d %H:%M:%S UTC')}")

    if created is not None and modified is not None:
        delta_seconds = int((modified - created).total_seconds())
        if delta_seconds < 0:
            findings.append(
                "[TIMESTAMP] Note: 'Last Modified' timestamp is earlier than 'Created' "
                "— metadata may be inconsistent."
            )
        else:
            minutes_total, seconds = divmod(delta_seconds, 60)
            hours, minutes         = divmod(minutes_total, 60)
            days, hours            = divmod(hours, 24)
            parts = []
            if days:
                parts.append(f"{days} day{'s' if days != 1 else ''}")
            if hours:
                parts.append(f"{hours} hr")
            parts.append(f"{minutes} min {seconds} sec")
            findings.append(
                f"[TIMESTAMP] Time between creation and last save: {' '.join(parts)}"
            )

    return findings
