#!/bin/bash
set -e  # Exit on any error

# Define directories
cur_dir="$PWD/src/layers/ffmpeg"
temp_dir="$(mktemp -d)"  # Creates a secure temporary directory

# Cleanup function
cleanup() {
    echo "Cleaning up..."
    rm -rf "$temp_dir"
}

# Set trap to ensure cleanup on script exit (success, error, or interrupt)
trap cleanup EXIT

# Create destination directory
echo "Creating destination directory..."
mkdir -p "$cur_dir/bin"

# Download and extract FFmpeg
echo "Downloading FFmpeg..."
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -P "$temp_dir"

echo "Extracting FFmpeg..."
cd "$temp_dir"
tar -xf ffmpeg-release-amd64-static.tar.xz

# Find the extracted directory
ffmpeg_dir=$(find . -maxdepth 1 -type d -name "ffmpeg-*-amd64-static" | head -n 1)

if [ -z "$ffmpeg_dir" ]; then
    echo "Error: FFmpeg directory not found after extraction"
    exit 1
fi

# Remove existing files in destination if they exist
echo "Preparing destination directory..."
rm -rf "$cur_dir/bin/"*

# Move files to destination
echo "Moving FFmpeg files to destination..."
mv "$ffmpeg_dir"/* "$cur_dir/bin/"

echo "FFmpeg download completed successfully"