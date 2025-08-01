# Release Script README

## Overview
The `release_script.py` automates the complete release process for HDL-FSM-Editor, ensuring consistency and proper versioning. It supports both **release builds** and **dev builds**.

## Prerequisites
- Python 3.9+
- Git (with proper remote configured)
- PyInstaller (already in dev dependencies)
- Working directory must be the project root

## Usage

### Release Build (Full Release)
Creates a complete release with git tagging. Requires clean git state.
```bash
python release_script.py --release
# or short form:
python release_script.py -r
```

### Dev Build (Development Build)
Creates a development build without git tagging. Allows dirty git state.
```bash
python release_script.py --dev
# or short form:
python release_script.py -d
```

### Dev Build with Custom Version
Override the version from CHANGELOG.md for dev builds:
```bash
python release_script.py --dev --version 4.12-dev
```

### Cleanup Build Artifacts
Remove PyInstaller build artifacts (dist/, build/, *.spec files):
```bash
python release_script.py --cleanup
```

## Build Types Comparison

| Feature | Release Build | Dev Build |
|---------|---------------|-----------|
| Git state | Must be clean | Can be dirty |
| Branch check | Warns if not main/master | No branch restrictions |
| Version consistency | Strict enforcement | Warning only |
| Date validation | Required | Optional (warning only) |
| Git tagging | Creates tag | No tagging |
| File naming | `HDL-FSM-Editor-4.12` | `HDL-FSM-Editor-4.12-dev-20250115-143022` |
| Archive naming | `HDL-FSM-Editor-4.12.zip` | `HDL-FSM-Editor-4.12-dev-20250115-143022.zip` |

## What the Script Does

### For Release Builds:
1. **Checks git status** - Ensures clean repository and main/master branch
2. **Parses CHANGELOG.md** - Finds latest version and validates date
3. **Verifies version consistency** - Ensures `src/main_window.py` matches CHANGELOG.md
4. **Checks git tag status** - Prompts if tag already exists
5. **Builds executable** - Uses PyInstaller to create standalone executable
6. **Creates release directory** - Organizes files in `releases/HDL-FSM-Editor-{version}/`
7. **Creates ZIP archive** - Packages everything for distribution
8. **Creates git tag** - Tags the release in git

### For Dev Builds:
1. **Checks git status** - Only verifies git repository exists
2. **Parses CHANGELOG.md** - Finds latest version (or uses override), date optional
3. **Verifies version consistency** - Warns but continues if mismatch
4. **Skips git tag check** - No tagging for dev builds
5. **Builds executable** - Uses PyInstaller to create standalone executable
6. **Creates release directory** - Includes timestamp in directory name
7. **Creates ZIP archive** - Includes timestamp in archive name
8. **Skips git tag creation** - No tagging for dev builds

### For Cleanup:
1. **Removes dist/ directory** - PyInstaller output directory
2. **Removes build/ directory** - PyInstaller build directory
3. **Removes *.spec files** - PyInstaller specification files

## Example Output

### Release Build:
```
🚀 Starting HDL-FSM-Editor Release Process
==================================================

🔍 Step 1: Checking git status
✅ Git repository is clean and ready for release

📋 Step 2: Parsing CHANGELOG.md
✅ Found version 4.12 with date 15.01.2025

🔍 Step 3: Verifying version consistency
✅ Version consistency verified: 4.12

🏷️  Step 4: Checking git tag status
✅ Git tag status verified for v4.12

🔨 Step 5: Building executable
🔨 Building executable with PyInstaller...
✅ Executable created: dist/HDL-FSM-Editor.exe

📁 Step 6: Creating release directory
✅ Release directory created: releases/HDL-FSM-Editor-4.12

📦 Step 7: Creating release archive
✅ Archive created: releases/HDL-FSM-Editor-4.12.zip

🏷️  Step 8: Creating git tag
✅ Git tag created: v4.12

==================================================
🎉 Release completed successfully!
📦 Release files:
   Directory: releases/HDL-FSM-Editor-4.12
   Archive: releases/HDL-FSM-Editor-4.12.zip
🏷️  Git tag: v4.12

💡 Next steps:
   1. Push the tag: git push origin v4.12
   2. Upload the archive to your release platform
   3. Update the website with the new version
```

### Dev Build:
```
🚀 Starting HDL-FSM-Editor Dev Build Process
==================================================

🔍 Step 1: Checking git status
✅ Git repository found (dev build mode)

📋 Step 2: Parsing CHANGELOG.md
✅ Found version 4.12 with date 15.01.2025

🔍 Step 3: Verifying version consistency
⚠️  Warning: Version mismatch (dev build)
   CHANGELOG.md: 4.12
   main_window.py: 4.11
   Continuing with dev build...

🏷️  Step 4: Checking git tag status
⏭️  Skipping git tag check (dev build)

🔨 Step 5: Building executable
🔨 Building executable with PyInstaller...
✅ Executable created: dist/HDL-FSM-Editor.exe

📁 Step 6: Creating release directory
✅ Release directory created: releases/HDL-FSM-Editor-4.12-dev-20250115-143022

📦 Step 7: Creating release archive
✅ Archive created: releases/HDL-FSM-Editor-4.12-dev-20250115-143022.zip

🏷️  Step 8: Creating git tag
⏭️  Skipping git tag creation (dev build)

==================================================
🎉 Dev Build completed successfully!
📦 Release files:
   Directory: releases/HDL-FSM-Editor-4.12-dev-20250115-143022
   Archive: releases/HDL-FSM-Editor-4.12-dev-20250115-143022.zip

💡 Next steps:
   1. Test the dev build
   2. Upload the archive for testing if needed
```

## Error Handling

### Common Errors and Solutions

#### Git Repository Not Clean (Release Build)
```
❌ Error: Git repository is not clean
   Please commit or stash all changes before creating a release
   Uncommitted changes:
     M src/main_window.py
```
**Solution**: Commit or stash changes before running release build

#### Wrong Branch (Release Build)
```
⚠️  Warning: Not on main/master branch (currently on feature-branch)
Continue anyway? (type 'yes' to confirm):
```
**Solution**: Switch to main/master branch or type 'yes' to continue

#### Version Mismatch
```
❌ Error: Version mismatch!
   CHANGELOG.md: 4.12
   main_window.py: 4.11
```
**Solution**: Update `_VERSION` in `src/main_window.py` to match CHANGELOG.md

#### Missing Date (Release Build)
```
❌ Error: Version 4.12 has no date assigned in CHANGELOG.md
```
**Solution**: Update the date in CHANGELOG.md from `xx.yy.2025` to actual date

#### Missing Date (Dev Build)
```
⚠️  Warning: Version 4.12 has no date assigned (dev build)
   Continuing with dev build...
```
**Solution**: This is just a warning for dev builds and will continue normally

#### Tag Already Exists
```
⚠️  Tag v4.12 already exists
Overwrite? (type 'yes' to confirm):
```
**Solution**: Type `yes` to overwrite, or any other input to cancel

#### PyInstaller Build Failure
```
❌ Error building executable: Command '['pyinstaller', ...]' returned non-zero exit status 1
```
**Solution**:
- Check PyInstaller is installed: `pip install pyinstaller`
- Ensure all dependencies are available
- Check for syntax errors in the code

## File Structure After Build

### Release Build:
```
releases/
├── HDL-FSM-Editor-4.12/
│   ├── HDL-FSM-Editor.exe
│   └── CHANGELOG.md
└── HDL-FSM-Editor-4.12.zip
```

### Dev Build:
```
releases/
├── HDL-FSM-Editor-4.12-dev-20250115-143022/
│   ├── HDL-FSM-Editor.exe
│   └── CHANGELOG.md
└── HDL-FSM-Editor-4.12-dev-20250115-143022.zip
```

## Manual Steps After Script

### For Release Builds:
1. **Push the git tag**:
   ```bash
   git push origin v4.12
   ```

2. **Upload to release platform** (GitHub, GitLab, etc.)

3. **Update website** with new version information

### For Dev Builds:
1. **Test the dev build** thoroughly

2. **Upload for testing** if needed

3. **No git operations** required

## Troubleshooting

### Git Issues
- Ensure you're in a git repository
- Check remote is configured: `git remote -v`
- Verify you have push permissions

### PyInstaller Issues
- Install dev dependencies: `pip install -e ".[dev]"`
- Check Python environment is correct
- Verify all imports are available

### File Permission Issues
- Ensure write permissions in project directory
- Check antivirus isn't blocking file operations

## Safety Features
- **Version validation** - Prevents releases with mismatched versions
- **Date validation** - Ensures changelog has proper date
- **Tag confirmation** - Prevents accidental tag overwrites
- **Build verification** - Confirms executable was created successfully
- **Archive validation** - Ensures ZIP file is not empty
- **Git state validation** - Ensures clean state for releases
- **Branch validation** - Warns about wrong branch for releases

## Script Dependencies
- Standard Python libraries only (no additional packages)
- Uses existing PyInstaller from dev dependencies
- Requires git to be available in PATH