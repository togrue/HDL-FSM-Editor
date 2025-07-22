#!/usr/bin/env python3
"""
HDL-FSM-Editor Automated Release Script
Handles the complete release process including version validation,
executable building, and git tagging.
Supports both release builds and dev builds.
"""

import argparse
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="HDL-FSM-Editor Release Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python release_script.py --release     # Create a full release with git tag
  python release_script.py --dev         # Create a dev build without git tag
  python release_script.py -r            # Short form for release
  python release_script.py -d            # Short form for dev build
  python release_script.py --cleanup     # Clean up PyInstaller build artifacts
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--release", "-r", action="store_true", help="Create a full release (requires clean git state, creates tag)"
    )
    group.add_argument("--dev", "-d", action="store_true", help="Create a dev build (allows dirty git state, no tag)")
    group.add_argument(
        "--cleanup", action="store_true", help="Clean up PyInstaller build artifacts (dist/, build/, *.spec)"
    )

    parser.add_argument("--version", help="Override version from CHANGELOG.md (for dev builds)")

    return parser.parse_args()


def check_git_status(is_release):
    """Check git repository status."""
    if is_release:
        # For releases, check if repository is clean
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)

        if result.stdout.strip():
            print("❌ Error: Git repository is not clean")
            print("   Please commit or stash all changes before creating a release")
            print("   Uncommitted changes:")
            for line in result.stdout.strip().split("\n"):
                if line:
                    print(f"     {line}")
            sys.exit(1)

        # Check if we're on main/master branch
        result = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, check=True)
        current_branch = result.stdout.strip()

        if current_branch not in ["main", "master"]:
            print(f"⚠️  Warning: Not on main/master branch (currently on {current_branch})")
            response = input("Continue anyway? (type 'yes' to confirm): ")
            if response.lower() != "yes":
                print("❌ Release cancelled by user")
                sys.exit(1)

        print("✅ Git repository is clean and ready for release")
    else:
        # For dev builds, just check if we're in a git repository
        try:
            subprocess.run(["git", "rev-parse", "--git-dir"], check=True, capture_output=True)
            print("✅ Git repository found (dev build mode)")
        except subprocess.CalledProcessError:
            print("⚠️  Warning: Not in a git repository (dev build mode)")


def parse_changelog_version(override_version=None, is_release=True):
    """Parse CHANGELOG.md and extract the latest version."""
    if override_version:
        print(f"✅ Using override version: {override_version}")
        return override_version

    changelog_path = Path("CHANGELOG.md")

    if not changelog_path.exists():
        print("❌ Error: CHANGELOG.md not found")
        sys.exit(1)

    with open(changelog_path, encoding="utf-8") as f:
        content = f.read()

    # Find the first version entry (not "Unreleased")
    version_pattern = r"## \[([0-9]+\.[0-9]+(?:\.[0-9]+)?)\] - (.+)"
    matches = re.findall(version_pattern, content)

    if not matches:
        print("❌ Error: No version entries found in CHANGELOG.md")
        sys.exit(1)

    version, date = matches[0]

    # Check if date is placeholder
    if date.strip() == "xx.yy.2025":
        if is_release:
            print(f"❌ Error: Version {version} has no date assigned in CHANGELOG.md")
            sys.exit(1)
        else:
            print(f"⚠️  Warning: Version {version} has no date assigned (dev build)")
            print("   Continuing with dev build...")

    if is_release:
        print(f"✅ Found version {version} with date {date}")
    else:
        print(f"✅ Found version {version} (dev build)")

    return version


def verify_version_consistency(version, is_release):
    """Verify that version in main_window.py matches CHANGELOG.md."""
    main_window_path = Path("src/main_window.py")

    if not main_window_path.exists():
        print("❌ Error: src/main_window.py not found")
        sys.exit(1)

    with open(main_window_path, encoding="utf-8") as f:
        content = f.read()

    # Find _VERSION line
    version_pattern = r'_VERSION = "([^"]+)"'
    match = re.search(version_pattern, content)

    if not match:
        print("❌ Error: _VERSION not found in src/main_window.py")
        sys.exit(1)

    file_version = match.group(1)

    if is_release and file_version != version:
        print("❌ Error: Version mismatch!")
        print(f"   CHANGELOG.md: {version}")
        print(f"   main_window.py: {file_version}")
        sys.exit(1)
    elif not is_release and file_version != version:
        print("⚠️  Warning: Version mismatch (dev build)")
        print(f"   CHANGELOG.md: {version}")
        print(f"   main_window.py: {file_version}")
        print("   Continuing with dev build...")

    print(f"✅ Version consistency verified: {version}")


def check_git_tag(version, is_release):
    """Check if git tag already exists and handle user confirmation."""
    if not is_release:
        print("⏭️  Skipping git tag check (dev build)")
        return

    tag_name = f"v{version}"

    # Check if tag exists
    result = subprocess.run(["git", "tag", "-l", tag_name], capture_output=True, text=True, check=True)

    if result.stdout.strip():
        print(f"⚠️  Tag {tag_name} already exists")
        response = input("Overwrite? (type 'yes' to confirm): ")

        if response.lower() != "yes":
            print("❌ Release cancelled by user")
            sys.exit(1)

        # Delete existing tag
        print(f"🗑️  Deleting existing tag {tag_name}")
        subprocess.run(["git", "tag", "-d", tag_name], check=True)
        subprocess.run(["git", "push", "origin", ":refs/tags/" + tag_name], check=True)

    print(f"✅ Git tag status verified for {tag_name}")


def build_executable():
    """Build executable using PyInstaller."""
    print("🔨 Building executable with PyInstaller...")

    # Clean previous build artifacts
    dist_path = Path("dist")
    build_path = Path("build")
    spec_path = Path("HDL-FSM-Editor.spec")

    if dist_path.exists():
        shutil.rmtree(dist_path)
    if build_path.exists():
        shutil.rmtree(build_path)
    if spec_path.exists():
        spec_path.unlink()

    # Build executable
    cmd = ["pyinstaller", "--onefile", "--windowed", "src/main.py", "--name", "HDL-FSM-Editor"]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error building executable: {e}")
        sys.exit(1)

    # Verify executable was created
    executable_path = dist_path / "HDL-FSM-Editor.exe"
    if not executable_path.exists():
        print("❌ Error: Executable was not created")
        sys.exit(1)

    print(f"✅ Executable created: {executable_path}")
    return executable_path


def create_release_directory(version, executable_path, is_release):
    """Create release directory and copy files."""
    if is_release:
        release_dir = Path("releases") / f"HDL-FSM-Editor-{version}"
    else:
        # For dev builds, include timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        release_dir = Path("releases") / f"HDL-FSM-Editor-{version}-dev-{timestamp}"

    # Create release directory
    release_dir.mkdir(parents=True, exist_ok=True)

    # Copy executable
    dest_executable = release_dir / "HDL-FSM-Editor.exe"
    shutil.copy2(executable_path, dest_executable)

    # Copy CHANGELOG.md
    changelog_dest = release_dir / "CHANGELOG.md"
    shutil.copy2("CHANGELOG.md", changelog_dest)

    print(f"✅ Release directory created: {release_dir}")
    return release_dir


def create_archive(version, release_dir, is_release):
    """Create ZIP archive of release directory."""
    if is_release:
        archive_name = f"HDL-FSM-Editor-{version}.zip"
    else:
        # For dev builds, include timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        archive_name = f"HDL-FSM-Editor-{version}-dev-{timestamp}.zip"

    archive_path = Path("releases") / archive_name

    # Remove existing archive if it exists
    if archive_path.exists():
        archive_path.unlink()

    # Create ZIP archive
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in release_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(release_dir)
                zipf.write(file_path, arcname)

    # Verify archive was created and has content
    if not archive_path.exists() or archive_path.stat().st_size == 0:
        print("❌ Error: Archive creation failed")
        sys.exit(1)

    print(f"✅ Archive created: {archive_path}")
    return archive_path


def create_git_tag(version, is_release):
    """Create git tag for the release."""
    if not is_release:
        print("⏭️  Skipping git tag creation (dev build)")
        return

    tag_name = f"v{version}"

    try:
        subprocess.run(["git", "tag", "-a", tag_name, "-m", f"Release {version}"], check=True)
        print(f"✅ Git tag created: {tag_name}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating git tag: {e}")
        sys.exit(1)


def cleanup_build_artifacts():
    """Clean up PyInstaller build artifacts."""
    print("🧹 Cleaning up PyInstaller build artifacts...")

    # Directories to remove
    dirs_to_remove = ["dist", "build"]
    # Files to remove
    files_to_remove = list(Path(".").glob("*.spec"))

    removed_count = 0

    # Remove directories
    for dir_name in dirs_to_remove:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"🗑️  Removed directory: {dir_name}")
            removed_count += 1
        else:
            print(f"ℹ️  Directory not found: {dir_name}")

    # Remove spec files
    for spec_file in files_to_remove:
        spec_file.unlink()
        print(f"🗑️  Removed file: {spec_file}")
        removed_count += 1

    if removed_count == 0:
        print("ℹ️  No build artifacts found to clean up")
    else:
        print(f"✅ Cleanup completed! Removed {removed_count} items")


def main():
    """Main release process."""
    args = parse_arguments()

    # Handle cleanup mode
    if args.cleanup:
        cleanup_build_artifacts()
        return

    is_release = args.release

    build_type = "Release" if is_release else "Dev Build"
    print(f"🚀 Starting HDL-FSM-Editor {build_type} Process")
    print("=" * 50)

    # Step 1: Check git status
    print("\n🔍 Step 1: Checking git status")
    check_git_status(is_release)

    # Step 2: Parse CHANGELOG.md
    print("\n📋 Step 2: Parsing CHANGELOG.md")
    version = parse_changelog_version(args.version, is_release)

    # Step 3: Verify version consistency
    print("\n🔍 Step 3: Verifying version consistency")
    verify_version_consistency(version, is_release)

    # Step 4: Check git tag status
    print("\n🏷️  Step 4: Checking git tag status")
    check_git_tag(version, is_release)

    # Step 5: Build executable
    print("\n🔨 Step 5: Building executable")
    executable_path = build_executable()

    # Step 6: Create release directory
    print("\n📁 Step 6: Creating release directory")
    release_dir = create_release_directory(version, executable_path, is_release)

    # Step 7: Create archive
    print("\n📦 Step 7: Creating release archive")
    archive_path = create_archive(version, release_dir, is_release)

    # Step 8: Create git tag
    print("\n🏷️  Step 8: Creating git tag")
    create_git_tag(version, is_release)

    print("\n" + "=" * 50)
    print(f"🎉 {build_type} completed successfully!")
    print("📦 Release files:")
    print(f"   Directory: {release_dir}")
    print(f"   Archive: {archive_path}")

    if is_release:
        print(f"🏷️  Git tag: v{version}")
        print("\n💡 Next steps:")
        print(f"   1. Push the tag: git push origin v{version}")
        print("   2. Upload the archive to your release platform")
        print("   3. Update the website with the new version")
    else:
        print("\n💡 Next steps:")
        print("   1. Test the dev build")
        print("   2. Upload the archive for testing if needed")


if __name__ == "__main__":
    main()
