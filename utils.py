import os
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_text_file(file_path, block_size=1024):
    """
    Determine if a file is a text file by checking for null bytes in the first block_size bytes.
    
    Args:
        file_path (str): Path to the file.
        block_size (int): Number of bytes to read (default: 1024).
    
    Returns:
        bool: True if the file is likely a text file, False if likely binary or unreadable.
    """
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(block_size)
            if b'\0' in chunk:
                return False  # Null bytes suggest a binary file
            return True  # No null bytes, likely a text file
    except Exception:
        return False  # Exclude files that can’t be read (e.g., permission issues)

def get_directory_tree(base_dir: str, max_depth: int = 2, 
                      ignore_dirs: List[str] = None, 
                      ignore_exts: List[str] = None) -> List[Dict[str, Any]]:
    """
    Generate a directory tree structure for the Dash Tree component.
    Respects the max depth and ignores specified directories and file extensions.
    
    Args:
        base_dir: Base directory to start tree from
        max_depth: Maximum depth to traverse
        ignore_dirs: List of directory names/paths to ignore
        ignore_exts: List of file extensions to ignore (without dot)
    
    Returns:
        List of dictionaries representing the tree structure
    """
    if ignore_dirs is None:
        ignore_dirs = []
    if ignore_exts is None:
        ignore_exts = []
    
    result = []
    
    def should_include_dir(dir_path: str) -> bool:
        """Check if directory should be included based on ignore list."""
        dir_name = os.path.basename(dir_path)
        rel_path = os.path.relpath(dir_path, base_dir)
        return not any(ignored in rel_path.split(os.sep) for ignored in ignore_dirs)
    
    def should_include_file(file_path: str) -> bool:
        """Check if file should be included based on extension ignore list."""
        _, ext = os.path.splitext(file_path)
        if ext.startswith('.'):
            ext = ext[1:]  # Remove the dot
        return ext not in ignore_exts
    
    def build_tree(dir_path: str, current_depth: int, rel_path: str = "") -> List[Dict[str, Any]]:
        """Recursively build tree structure."""
        if current_depth > max_depth:
            return []
        
        items = []
        try:
            for name in sorted(os.listdir(dir_path)):
                full_path = os.path.join(dir_path, name)
                item_rel_path = os.path.join(rel_path, name) if rel_path else name
                
                if os.path.isdir(full_path):
                    if should_include_dir(full_path):
                        children = build_tree(full_path, current_depth + 1, item_rel_path)
                        if children or current_depth < max_depth:
                            items.append({
                                "label": name,
                                "value": item_rel_path,
                                "children": children,
                                "icon": "folder"
                            })
                else:
                    if should_include_file(full_path):
                        items.append({
                            "label": name,
                            "value": item_rel_path,
                            "icon": "file"
                        })
        except (PermissionError, FileNotFoundError) as e:
            logger.warning(f"Error accessing {dir_path}: {e}")
        
        return items
    
    try:
        result = build_tree(base_dir, 0)
    except Exception as e:
        logger.error(f"Failed to build directory tree: {e}")
    
    return result

def read_file_safely(file_path: str) -> str:
    """
    Read a file with proper error handling.
    
    Args:
        file_path: Path to the file
    
    Returns:
        File content as string or error message
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            # Try with a different encoding
            with open(file_path, "r", encoding="latin-1") as f:
                return f.read()
        except Exception as e:
            return f"Error: Could not read file due to encoding issues: {e}"
    except Exception as e:
        return f"Error: Could not read file: {e}"

def build_super_prompt(files: List[str], base_dir: str, user_prompt: str = "", 
                      abort_threshold: int = 50) -> str:
    """
    Build the super prompt from selected files with threshold checking.
    
    Args:
        files: List of file paths (relative to base_dir)
        base_dir: Base directory path
        user_prompt: User's initial prompt text
        abort_threshold: Maximum number of files before aborting
    
    Returns:
        Formatted super prompt string
    """
    if len(files) > abort_threshold:
        return (f"Error: Too many files selected ({len(files)}). " 
                f"The maximum is {abort_threshold}. Please select fewer files.")
    
    super_prompt = ""
    
    # Add user prompt if provided
    if isinstance(user_prompt, str) and len(user_prompt) > 0:
        super_prompt = f"{user_prompt}\n\n"
    
    # Add context from selected files
    if files:
        for file in files:
            file_path = os.path.join(base_dir, file)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                content = read_file_safely(file_path)
                file_ext = os.path.splitext(file)[1][1:]  # Get extension without dot
                if not file_ext:
                    file_ext = "text"
                super_prompt += f"`{file}`:\n```{file_ext}\n{content}\n```\n\n"
    
    return super_prompt