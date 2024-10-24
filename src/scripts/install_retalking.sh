#!/bin/bash
set -e  # Exit on any error

# Define directories
cur_dir="$PWD/src/retalking/code"
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
mkdir -p "$cur_dir"

# Clone repository
echo "Cloning video-retalking repository..."
git clone https://github.com/OpenTalker/video-retalking "$temp_dir"

# Remove existing directories if they exist
echo "Removing existing directories..."
for dir in models third_part utils; do
    if [ -d "$cur_dir/$dir" ]; then
        rm -rf "$cur_dir/$dir"
    fi
done

# Move required directories
echo "Moving required directories..."
for dir in models third_part utils; do
    if [ -d "$temp_dir/$dir" ]; then
        mv "$temp_dir/$dir" "$cur_dir/"
    else
        echo "Warning: Directory '$dir' not found in cloned repository"
    fi
done

echo "Successfully downloaded video-retalking"