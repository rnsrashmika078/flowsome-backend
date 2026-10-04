import os

desktop_path = os.path.expanduser('~') + os.sep + 'Desktop'

if os.path.exists(desktop_path):
    image_files = []
    for filename in os.listdir(desktop_path):
        if os.path.isfile(os.path.join(desktop_path, filename)) and filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            image_files.append(filename)

    if image_files:
        print("Image files in Desktop:")
        for img in image_files:
            print(img)
    else:
        print("No image files found in Desktop.")
else:
    print("Desktop directory not found.")
import os

desktop_path = os.path.expanduser('~') + os.sep + 'Desktop'

if os.path.exists(desktop_path):
    image_files = []
    for filename in os.listdir(desktop_path):
        if os.path.isfile(os.path.join(desktop_path, filename)) and filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            image_files.append(filename)

    if image_files:
        print("Image files in Desktop:")
        for img in image_files:
            print(img)
    else:
        print("No image files found in Desktop.")
else:
    print("Desktop directory not found.")