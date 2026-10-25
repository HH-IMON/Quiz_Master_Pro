import shutil
import os
import zipfile

def zip_project(output_filename):
    # Files/Dirs to exclude
    EXCLUDE = {
        '__pycache__', '.git', '.vscode', '.idea', 'env', 'venv', 
        'node_modules', '*.pyc', '*.pyo', '*.pyd', 
        'deploy_package.py', 'quiz_master_pro_ready.zip',
        '.gemini' # Exclude my own brain directory
    }
    
    # Get current directory
    source_dir = os.getcwd()
    
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Modify dirs in-place to filter excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE and not d.startswith('.')]
            
            for file in files:
                if file not in EXCLUDE and not file.endswith('.zip') and not file.endswith('.pyc'):
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)
                    print(f"Added: {arcname}")

if __name__ == '__main__':
    output_zip = 'quiz_master_pro_deploy_ready.zip'
    print(f"Creating {output_zip}...")
    zip_project(output_zip)
    print(f"Successfully created {output_zip}")
