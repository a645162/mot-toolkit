#!/usr/bin/env zsh
set -e
# This script is used to build Nuitka on macOS.

cd ..||exit

# Check directory 'src' is Exist

if [ ! -d "src" ]; then
  echo "Directory 'src' is not exist."
  exit 1
fi

python -m nuitka --version

# Build
python -m nuitka \
  --output-filename=mot-toolkit \
  --output-dir="./Build/Output/macOS" \
  --company-name="Haomin Kong" \
  --standalone \
  --remove-output \
  --enable-plugin=pyside6 \
  --macos-create-app-bundle \
  --macos-app-name=mot-toolkit \
  --macos-app-icon="./Resources/PySide6/Logo/Icon/macOS/Logo.icns" \
  src/mot-toolkit.py
