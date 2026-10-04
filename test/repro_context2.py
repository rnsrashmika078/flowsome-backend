import os

def list_files_by_type(directory):
    """Lists image, PDF, and text files in the given directory."""
    file_types = {
        'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'],
        'pdf': ['.pdf'],
        'text': ['.txt']
    }
    found_files = {
        'image': [],
        'pdf': [],
        'text': []
    }

    if not os.path.isdir(directory):
        print(f"Error: Directory not found at {directory}")
        return found_files

    try:
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                # Check for image files
                if filename.lower().endswith(file_types['image']):
                    found_files['image'].append(filename)
                # Check for PDF files
                elif filename.lower().endswith(file_types['pdf']):
                    found_files['pdf'].append(filename)
                # Check for text files
                elif filename.lower().endswith(file_types['text']):
                    found_files['text'].append(filename)

    except Exception as e:
        print(f"An error occurred: {e}")

    return found_files

# Define the desktop directory
desktop_path = os.path.expanduser("~/Desktop")

# List the files
results = list_files_by_type(desktop_path)

# Print the results
print("--- Image Files ---")
for img in results['image']:
    print(img)

print("\n--- PDF Files ---")
for pdf in results['pdf']:
    print(pdf)

print("\n--- Text Files ---")
for txt in results['text']:
    print(txt)
import os

def list_files_by_type(directory):
    """Lists image, PDF, and text files in the given directory."""
    file_types = {
        'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'],
        'pdf': ['.pdf'],
        'text': ['.txt']
    }
    found_files = {
        'image': [],
        'pdf': [],
        'text': []
    }

    if not os.path.isdir(directory):
        print(f"Error: Directory not found at {directory}")
        return found_files

    try:
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if os.path.isfile(filepath):
                # Check for image files
                if filename.lower().endswith(file_types['image']):
                    found_files['image'].append(filename)
                # Check for PDF files
                elif filename.lower().endswith(file_types['pdf']):
                    found_files['pdf'].append(filename)
                # Check for text files
                elif filename.lower().endswith(file_types['text']):
                    found_files['text'].append(filename)

    except Exception as e:
        print(f"An error occurred: {e}")

    return found_files

# Define the desktop directory
desktop_path = os.path.expanduser("~/Desktop")

# List the files
results = list_files_by_type(desktop_path)

# Print the results
print("--- Image Files ---")
for img in results['image']:
    print(img)

print("\n--- PDF Files ---")
for pdf in results['pdf']:
    print(pdf)

print("\n--- Text Files ---")
for txt in results['text']:
    print(txt)