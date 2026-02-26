
import docx

def scrape_metadata(file_path):
    """
    Analyzes the core metadata of a .docx file for AI-related keywords.
    
    Args:
        file_path (str): The path to the .docx file.

    Returns:
        list: A list of strings containing the metadata analysis findings.
    """
    findings = []
    try:
        document = docx.Document(file_path)
        core_properties = document.core_properties
        ai_keywords = ["ai", "artificial intelligence", "chatgpt", "gpt-3", "gpt-4", "dall-e", "midjourney", "stable diffusion", "copilot"]

        findings.append("--- Metadata Analysis ---")
        if core_properties.author and any(k in core_properties.author.lower() for k in ai_keywords):
            findings.append(f"Potential AI keyword found in author: {core_properties.author}")
        if core_properties.last_modified_by and any(k in core_properties.last_modified_by.lower() for k in ai_keywords):
            findings.append(f"Potential AI keyword found in last_modified_by: {core_properties.last_modified_by}")
        if core_properties.comments and any(k in core_properties.comments.lower() for k in ai_keywords):
            findings.append(f"Potential AI keyword found in comments: {core_properties.comments}")
        
        if len(findings) == 1: # Only the header was added
            findings.append("No AI-related keywords found in metadata.")

    except Exception as e:
        findings.append(f"An unexpected error occurred during metadata scan: {e}")
        
    return findings
