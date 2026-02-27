
import zipfile
import xml.etree.ElementTree as ET


def extract_comments(file_path):
    """
    Extracts all inline comments from word/comments.xml inside the .docx ZIP.
    Each comment reports its author, date, and text content.

    Args:
        file_path (str): The path to the .docx file.

    Returns:
        list: Finding strings for each comment found, or a "none found" message.
    """
    findings = []
    try:
        with zipfile.ZipFile(file_path, 'r') as z:
            if 'word/comments.xml' not in z.namelist():
                findings.append("[COMMENT] No comments found in document.")
                return findings

            with z.open('word/comments.xml') as comments_xml:
                root = ET.parse(comments_xml).getroot()
                w = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

                comments = root.findall(f'{w}comment')
                if not comments:
                    findings.append("[COMMENT] No comments found in document.")
                    return findings

                findings.append(f"[COMMENT] {len(comments)} comment(s) found.")
                for comment in comments:
                    author = comment.attrib.get(f'{w}author', 'Unknown')
                    date   = comment.attrib.get(f'{w}date', '')
                    if date and 'T' in date:
                        date = date.split('T')[0]

                    texts = [r.text for r in comment.iter(f'{w}t') if r.text]
                    body  = ' '.join(texts).strip()
                    if len(body) > 120:
                        body = body[:117] + '...'

                    findings.append(
                        f'[COMMENT] Author: "{author}" | Date: {date} | Text: "{body}"'
                    )

    except zipfile.BadZipFile:
        findings.append("[COMMENT] Could not read document — file is not a valid .docx.")
    except Exception as e:
        findings.append(f"[COMMENT] Error extracting comments: {e}")

    return findings
