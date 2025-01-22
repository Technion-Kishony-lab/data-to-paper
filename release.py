"""
Cross-platform release script with PyPI authentication handling and state restoration
You need to add you PyPI credentials to ~/.pypirc file
Usage: python release.py <new-version> [--test]
"""

import re
import sys
import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List

# Configuration
PYPI_REPO = "pypi"  # Default repository
TEST_PYPI_REPO = "testpypi"
PYPROJECT_FILE = "pyproject.toml"
DIST_DIRS = ["dist", "build", "*.egg-info"]


@dataclass
class RepoState:
    branch: str
    commit: str
    tags: List[str]
    initial_version: Optional[str] = None


def get_current_state() -> RepoState:
    """Capture current repository state"""
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
        ).strip()
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
        tags = (
            subprocess.check_output(["git", "tag", "--list"], text=True)
            .strip()
            .splitlines()
        )

        # Get current version from pyproject.toml
        content = Path(PYPROJECT_FILE).read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*"(.+)"', content, flags=re.MULTILINE)
        initial_version = match.group(1) if match else None

        return RepoState(branch, commit, tags, initial_version)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("Failed to capture repository state") from e


def restore_state(original: RepoState, new_version: str):
    """Restore repository to original state"""
    print("\n⏪ Attempting to restore repository state...")

    try:
        # Reset to original commit
        subprocess.run(
            ["git", "reset", "--hard", original.commit],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Delete release tag if created
        if (
            new_version
            in subprocess.check_output(["git", "tag"], text=True).splitlines()
        ):
            subprocess.run(
                ["git", "tag", "-d", new_version],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print(f"🗑️  Deleted tag {new_version}")

        # Checkout original branch if needed
        current_branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
        ).strip()
        if current_branch != original.branch:
            subprocess.run(
                ["git", "checkout", original.branch],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        # Restore original version if pyproject.toml was modified
        if original.initial_version:
            content = Path(PYPROJECT_FILE).read_text(encoding="utf-8")
            current_version = re.search(
                r'^version\s*=\s*"(.+)"', content, flags=re.MULTILINE
            )
            if current_version and current_version.group(1) != original.initial_version:
                update_pyproject_version(original.initial_version)
                print(f"🔄 Restored original version {original.initial_version}")

        print("✅ Repository state restored")
    except subprocess.CalledProcessError as e:
        print(f"❌ Partial restoration failed. Manual cleanup required: {str(e)}")


def validate_version(version: str):
    """Validate semantic version format X.Y.Z"""
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        raise ValueError(f"Invalid version format: {version}. Use X.Y.Z format")


def update_pyproject_version(version: str):
    """Update version in pyproject.toml"""
    path = Path(PYPROJECT_FILE)
    content = path.read_text(encoding="utf-8")
    updated = re.sub(
        r'^version\s*=\s*".+"\s*$',
        f'version = "{version}"',
        content,
        flags=re.MULTILINE,
    )
    path.write_text(updated, encoding="utf-8")


def check_git_clean():
    """Ensure working directory is clean"""
    status = subprocess.check_output(
        ["git", "status", "--porcelain"], text=True
    ).strip()
    if status:
        raise RuntimeError("Working directory is not clean. Commit or stash changes.")


def run_command(cmd: list, capture=False):
    """Run shell command with error handling"""
    try:
        result = subprocess.run(
            cmd,
            check=True,
            text=True,
            capture_output=capture,
        )
        return result.stdout.strip() if capture else None
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Command failed ({' '.join(cmd)}): {e.stderr or e.stdout}"
        ) from e


def publish_package(test: bool):
    """Build and upload package to PyPI"""
    # Clean previous builds
    for pattern in DIST_DIRS:
        for path in Path().glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)

    # Build package
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "build"])
    run_command([sys.executable, "-m", "build"])

    # Upload with twine
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "twine"])

    twine_cmd = [sys.executable, "-m", "twine", "upload"]
    if test:
        twine_cmd.extend(["--repository", TEST_PYPI_REPO])

    twine_cmd.append("dist/*")
    run_command(twine_cmd)


def main():
    original_state: Optional[RepoState] = None
    new_version: Optional[str] = None
    should_restore = False

    try:
        # Parse arguments
        if len(sys.argv) < 2:
            print(__doc__)
            sys.exit(1)

        new_version = sys.argv[1]
        test_mode = "--test" in sys.argv

        # Capture initial state before any changes
        original_state = get_current_state()
        print(
            f"📸 Captured initial state: {original_state.commit[:7]} on {original_state.branch}"
        )

        # Validate environment
        validate_version(new_version)
        check_git_clean()

        should_restore = True

        # Update version
        update_pyproject_version(new_version)
        run_command(["git", "add", PYPROJECT_FILE])
        run_command(["git", "commit", "-m", f"version {new_version}"])
        run_command(["git", "tag", "-a", new_version, "-m", f"Version {new_version}"])

        # Push changes
        run_command(["git", "push", "origin", "main"])
        run_command(["git", "push", "origin", new_version])

        # Publish package
        publish_package(test_mode)

        # Cleanup
        for pattern in DIST_DIRS:
            for path in Path().glob(pattern):
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)

        print(f"\n✅ Successfully released version {new_version}!")

    except KeyboardInterrupt:
        print("\n🚨 Process interrupted by user")
        if original_state and new_version and should_restore:
            restore_state(original_state, new_version)
        elif not original_state:
            print("🚨 No restoration possible - no state captured")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if original_state and new_version and should_restore:
            restore_state(original_state, new_version)
        elif not original_state:
            print("🚨 No restoration possible - no state captured")
        sys.exit(1)


if __name__ == "__main__":
    main()
