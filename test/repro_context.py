import os
import pathlib

# Determine the path to the Desktop folder
desktop_path = pathlib.Path.home() / "Desktop"

if not desktop_path.is_dir():
    print(f"Error: Desktop directory not found at {desktop_path}")
else:
    print(f"Listing images in: {desktop_path}")
    image_files = []
    # Iterate over files in the desktop directory
    for item in desktop_path.iterdir():
        if item.is_file():
            # Check for common image extensions (case-insensitive)
            if item.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
                image_files.append(item.name)

    if image_files:
        print("\nFound images:")
        for img in image_files:
            print(f"- {img}")
    else:
        print("\nNo common image files found in the Desktop directory.")