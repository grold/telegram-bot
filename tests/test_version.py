from unittest.mock import patch
import subprocess
from config import get_version, get_git_branch

def test_get_git_branch_success():
    with patch("subprocess.check_output") as mock_run:
        mock_run.return_value = b"feature-branch\n"
        assert get_git_branch() == "feature-branch"

def test_get_git_branch_failure():
    with patch("subprocess.check_output") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        assert get_git_branch() is None

def test_get_version_with_branch():
    with patch("config.get_git_branch") as mock_branch:
        mock_branch.return_value = "master"
        # We need to read the actual version from pyproject.toml in the test or mock it
        version = get_version()
        assert "-master" in version

def test_get_version_without_branch():
    with patch("config.get_git_branch") as mock_branch:
        mock_branch.return_value = None
        version = get_version()
        assert "-" not in version
        assert version != "unknown"

def test_get_version_with_head_branch():
    # If git returns HEAD (detached), we should just show the version
    with patch("config.get_git_branch") as mock_branch:
        mock_branch.return_value = "HEAD"
        version = get_version()
        assert "-" not in version
