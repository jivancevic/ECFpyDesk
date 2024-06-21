import os

def print_project_structure(root_dir):
    for root, dirs, files in os.walk(root_dir, topdown=True):
        level = root.replace(root_dir, '').count(os.sep)
        indent = '+' * level
        folder_name = os.path.basename(root)
        if folder_name in ["venv", ".git"]:
            # Exclude the directory from further traversal
            dirs.clear()
            continue
        print(f"{indent}{folder_name}/")
        sub_indent = '+' * (level + 1)
        for file in files:
            print(f"{sub_indent}{file}")

# Example usage
root_directory = '.'
print_project_structure(root_directory)


