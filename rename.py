import os

# Add your own path as argument

# === Configuration ===
folder_path = r"C:\Users\dylan\Documents\Computer science\Computer Science Year 3\Image identification v2\images\All images"  # 👈 Change this to your folder path
start_number = 1                          # 👈 Change this to your starting number
# ======================

def rename_images(folder_path, start_number):
    # Supported image file extensions
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')

    # Get all image files in the folder
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(image_extensions)]

    # Sort files alphabetically (optional, for consistent order)
    files.sort()

    # Start renaming
    counter = start_number
    for filename in files:
        ext = os.path.splitext(filename)[1]  # Get file extension
        new_name = f"Image_{counter}{ext}"
        old_path = os.path.join(folder_path, filename)
        new_path = os.path.join(folder_path, new_name)
        os.rename(old_path, new_path)
        print(f"Renamed: {filename} → {new_name}")
        counter += 1

    print("\n✅ All images renamed successfully.")

# Run the renaming function
if __name__ == "__main__":
    if not os.path.isdir(folder_path):
        print("Error: The given folder path does not exist or is not a directory.")
    else:
        rename_images(folder_path, start_number)
