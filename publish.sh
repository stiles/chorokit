#!/bin/bash

# A script to automate the publishing of the chorokit package to PyPI.
# Exit immediately if a command exits with a non-zero status.
set -e

echo "Starting the chorokit publishing process..."
echo "========================================"

# --- 1. Version Check ---
# Extract version from pyproject.toml
VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = //' | sed 's/"//g' | xargs)

if [ -z "$VERSION" ]; then
    echo "Error: Could not find version in pyproject.toml"
    exit 1
fi

echo "You are about to publish version '$VERSION'."
echo

# --- 2. Git Status Check ---
echo "--- Git Status Check ---"
if ! git diff-index --quiet HEAD --; then
    echo "Warning: Uncommitted changes detected in your working directory."
    read -p "Are you sure you want to continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Publishing cancelled. Please commit your changes."
        exit 1
    fi
fi
echo "Git status is clean."

# --- 3. Pre-flight Checklist ---
echo "--- Pre-flight Checklist ---"
read -p "Have you updated the README.md with any new features or changes? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Publishing cancelled. Please update the README.md."
    exit 1
fi

read -p "Have you tested the ColorBrewer palettes and layout system? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Publishing cancelled. Please test the core features."
    exit 1
fi

# --- 4. Confirmation ---
read -p "You are ready to publish version '$VERSION'. Is this correct? (y/n) " -n 1 -r
echo # Move to a new line

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Publishing cancelled."
    exit 1
fi

# --- 5. Run Basic Tests ---
echo "--- Running Basic Tests ---"
echo "Testing imports..."
if ! python3 -c "from chorokit import plot_choropleth, LegendConfig, LayoutConfig; print('✅ Imports successful')"; then
    echo "Error: Import test failed. Please fix before publishing."
    exit 1
fi

echo "Testing ColorBrewer palettes..."
if ! python3 -c "from chorokit.palettes import get_palette_colors; colors = get_palette_colors('Blues', 5); assert len(colors) == 5; print('✅ ColorBrewer test passed')"; then
    echo "Error: ColorBrewer test failed. Please fix before publishing."
    exit 1
fi

echo "✅ Basic tests passed."

# --- 6. Prerequisite Check ---
echo "Checking for required tools..."
command -v python3 >/dev/null 2>&1 || { echo >&2 "Error: python3 is not installed. Aborting."; exit 1; }
python3 -m pip show build >/dev/null 2>&1 || { echo >&2 "Error: 'build' is not installed. Run 'pip install build'. Aborting."; exit 1; }
python3 -m pip show twine >/dev/null 2>&1 || { echo >&2 "Error: 'twine' is not installed. Run 'pip install twine'. Aborting."; exit 1; }
echo "Tools found."
HAS_GH=$(command -v gh >/dev/null 2>&1 && echo "true" || echo "false")

# --- 7. Clean and Build ---
echo "Cleaning up previous builds..."
rm -rf build dist chorokit.egg-info
echo "Building the package..."
python3 -m build
echo "Build complete. New files are in the dist/ directory:"
ls -l dist

# --- 8. Publish ---
echo
echo "What would you like to do?"
select choice in "Publish to TestPyPI" "Publish to PyPI (Official)" "Cancel"; do
    case $choice in
        "Publish to TestPyPI" )
            echo "Preparing to upload to TestPyPI..."
            if [ -z "$PYPI_TEST" ]; then
                echo "Error: PYPI_TEST environment variable is not set."
                echo "Please set your TestPyPI token: export PYPI_TEST=your_test_token"
                exit 1
            fi
            echo "Uploading to TestPyPI..."
            python3 -m twine upload --repository-url https://test.pypi.org/legacy/ -u __token__ -p "$PYPI_TEST" dist/*
            echo
            echo "✅ Successfully published to TestPyPI."
            echo "You can view the package at: https://test.pypi.org/project/chorokit/$VERSION/"
            echo "You can install it using: python3 -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple chorokit==$VERSION"
            break
            ;;
        "Publish to PyPI (Official)" )
            read -p "⚠️  Are you sure you want to publish to the OFFICIAL PyPI? This is permanent. (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo "Preparing to upload to official PyPI..."
                if [ -z "$PYPI" ]; then
                    echo "Error: PYPI environment variable is not set."
                    echo "Please set your PyPI token: export PYPI=your_pypi_token"
                    exit 1
                fi
                echo "Uploading to PyPI..."
                python3 -m twine upload -u __token__ -p "$PYPI" dist/*
                echo
                echo "✅ Successfully published to PyPI!"
                echo "Your package is now live at: https://pypi.org/project/chorokit/$VERSION/"
                echo "Users can install it with: pip install chorokit"
                
                # --- 9. GitHub Release ---
                echo
                read -p "Do you want to create a GitHub release for v$VERSION? (y/n) " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    if [ "$HAS_GH" = "false" ]; then
                        echo "Warning: GitHub CLI ('gh') not found. Cannot create release automatically."
                        echo "Please create the release manually: https://github.com/mstiles/chorokit/releases/new"
                        exit 0
                    fi

                    echo "Creating GitHub release..."
                    TAG="v$VERSION"
                    
                    # Create release notes
                    NOTES="# Chorokit v$VERSION

## 🎨 ColorBrewer Integration
- Complete ColorBrewer 2.0 palette support (35 palettes)
- Sequential, diverging, and qualitative color schemes
- Discrete color classes (3-12 colors per palette)
- Proper attribution to Cynthia Brewer and Penn State

## 🎯 Professional Layout System  
- Publication-ready spacing and typography
- Top and bottom legend placement (no more awkward right legends)
- Smart auto-projection for US data
- Clean margins and consistent hierarchy

## 🚀 Easy to Use
- Single function API: \`plot_choropleth()\`
- ColorBrewer palettes: \`palette=('Blues', 7)\`
- Auto-classification: \`scheme='natural'\`
- CLI support: \`chorokit data.geojson column --palette Blues:7\`

## 📦 Installation
\`\`\`bash
pip install chorokit
\`\`\`"
                    
                    echo "Tagging release with $TAG..."
                    git tag "$TAG"
                    git push origin "$TAG"

                    echo "Creating release on GitHub and uploading assets..."
                    gh release create "$TAG" dist/* --title "Chorokit $TAG" --notes "$NOTES"
                    echo "✅ GitHub release created successfully."
                fi
            else
                echo "Publishing to official PyPI cancelled."
            fi
            break
            ;;
        "Cancel" )
            echo "Operation cancelled."
            break
            ;;
        * )
            echo "Invalid option. Please choose 1, 2, or 3."
            ;;
    esac
done

echo "========================================"
echo "Publishing process finished."
