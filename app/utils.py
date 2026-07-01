import re

def normalize_header(header):
    """
    Normalizes a column header:
    - Converts to lowercase
    - Trims whitespaces
    - Replaces interior spaces/hyphens with a single underscore
    - Strips special characters (anything not alphanumeric or underscore)
    - Trims leading/trailing underscores
    """
    if not header:
        return ""
    
    # Lowercase & trim
    val = str(header).strip().lower()
    
    # Replace spaces and hyphens with underscores
    val = re.sub(r'[\s\-]+', '_', val)
    
    # Strip special characters (keep only a-z, 0-9, and _)
    val = re.sub(r'[^a-z0-9_]', '', val)
    
    # Collapse multiple consecutive underscores
    val = re.sub(r'_+', '_', val)
    
    # Strip leading/trailing underscores
    val = val.strip('_')
    
    return val
