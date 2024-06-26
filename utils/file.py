import os

def delete_file_if_exists(file_path):
        if os.path.exists(file_path):
            os.remove(file_path)

def delete_all_files_in_directory(directory):
    # Check if the directory exists
    if not os.path.exists(directory):
        print(f"Directory '{directory}' does not exist.")
        return
    
    for root, dirs, files in os.walk(directory, topdown=False):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                os.remove(file_path)  # Delete the file
                print(f"Deleted file: {file_path}")
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")
        
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            try:
                os.rmdir(dir_path)  # Delete the directory
                print(f"Deleted directory: {dir_path}")
            except Exception as e:
                print(f"Error deleting directory {dir_path}: {e}")

def create_directory(directory_path):
    try:
        os.makedirs(directory_path)
        print(f"Directory created successfully: {directory_path}")
    except FileExistsError:
        pass
    except Exception as e:
        print(f"Error creating directory '{directory_path}': {e}")