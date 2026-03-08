import re

def validate_youtube_link(url: str) -> bool:
    """
    Checks if a given string is a valid YouTube URL format.
    """
    if not url:
        return False
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=|shorts/)?([^&=%\?]{11})')
    
    return re.match(youtube_regex, url) is not None


def format_bytes(size):
    """
    Convert bytes to a human-readable string (e.g., KB, MB, GB).
    If size is None, returns a clear label.
    """
    if size is None or size <= 0:
        return "Unknown Size"
    
    # Ensure size is an integer before calculation
    try:
        size = int(size)
    except (ValueError, TypeError):
        return "Unknown Size"
        
    # The 'powers' for Kilo, Mega, Giga, etc.
    power = 1024
    n = 0
    # Labels for the corresponding powers
    labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    
    # Use f-string to indicate approximation if the size was an estimate
    prefix = "~" if size % power != 0 and n == 0 else ""

    while size >= power and n < len(labels) - 1:
        size /= power
        n += 1
        
    # If the size came from an approximation, include the '~' prefix
    return f"{prefix}{size:.2f} {labels.get(n, 'PB')}"