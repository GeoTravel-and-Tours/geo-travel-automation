import os
import subprocess
from src.utils.logger import GeoLogger

logger = GeoLogger("GitUtils")

def get_current_branch():
    """Get current git branch name (works for CircleCI, GitHub Actions, or local)"""
    try:
        # Try to get branch from environment (CI/CD)
        branch = (
            os.getenv("BRANCH")
            or os.getenv("GIT_BRANCH")
            or os.getenv("CIRCLE_BRANCH")
            or os.getenv("GITHUB_REF_NAME")  # ✅ GitHub Actions
        )

        if branch:
            if branch.startswith("refs/heads/"):
                branch = branch.replace("refs/heads/", "")
            return branch.upper()

        # Fallback to git command (local)
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        branch = result.stdout.strip()
        return branch.upper() if branch else "MAIN"

    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("Could not determine git branch, using 'MAIN' as default")
        return "MAIN"


def get_commit_hash():
    """Get current commit hash"""
    try:
        commit = (
            os.getenv("CIRCLE_SHA1")
            or os.getenv("GITHUB_SHA")  # ✅ GitHub Actions
        )
        if commit:
            return commit[:7]
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("Could not determine commit hash")
        return "UNKNOWN"


def setup_git_metadata():
    """Setup git-related metadata automatically"""
    branch = get_current_branch()
    commit_hash = get_commit_hash()

    os.environ["BRANCH"] = branch
    os.environ["COMMIT_HASH"] = commit_hash

    logger.info(f"Git Metadata - Branch: {branch}, Commit: {commit_hash}")
    return {"branch": branch, "commit_hash": commit_hash}
