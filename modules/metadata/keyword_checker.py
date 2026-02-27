
AI_KEYWORDS = [
    "ai", "artificial intelligence", "chatgpt",
    "gpt-3", "gpt-4", "dall-e", "midjourney",
    "stable diffusion", "copilot"
]

def check_keywords(props):
    """
    Scans 7 core property text fields for AI-related keywords.

    Args:
        props: A python-docx CoreProperties object.

    Returns:
        list: A list of finding strings, one per keyword match found.
    """
    findings = []
    fields_to_scan = [
        ("author",           props.author),
        ("last_modified_by", props.last_modified_by),
        ("comments",         props.comments),
        ("title",            props.title),
        ("subject",          props.subject),
        ("keywords",         props.keywords),
        ("category",         props.category),
    ]
    for field_name, value in fields_to_scan:
        if value and any(k in value.lower() for k in AI_KEYWORDS):
            findings.append(f"[KEYWORD] Match found in '{field_name}': {value}")
    return findings
