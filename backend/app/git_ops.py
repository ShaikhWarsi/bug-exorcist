import git
import os
from typing import Optional
from pathlib import Path

def apply_fix_to_repo(
    repo_path: str, bug_id: str, file_path: str, fixed_code: str
) -> str:
    """
    Applies a fix to the repository by creating a new branch, updating the file, and committing.
    """
    try:
        # Validate paths internally as a second line of defense
        repo_dir = Path(repo_path).resolve()
        if not repo_dir.is_dir():
            return f"Error: {repo_path} is not a valid directory"
            
        target_file = (repo_dir / file_path).resolve()
        if repo_dir not in target_file.parents and repo_dir != target_file:
            return f"Error: Path traversal detected in {file_path}"

        repo = git.Repo(repo_path)
        
    

        branch_name = f"fix/bug-{bug_id}"
        
        # Create or checkout branch
        if branch_name in repo.heads:
            current = repo.heads[branch_name]
            current.checkout()
        else:
            current = repo.create_head(branch_name)
            current.checkout()
            
        # Full path to the file (already validated above)
        full_file_path = str(target_file)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
        
        # Write the fixed code
        with open(full_file_path, "w", encoding="utf-8") as f:
            f.write(fixed_code)
            
        # Git operations
        repo.index.add([full_file_path])
        repo.index.commit(f"fix: applied fix for bug {bug_id}")
        
        return f"Success: Fix applied on branch {branch_name}"
        
    except Exception as e:
        return f"Error applying fix: {str(e)}"
