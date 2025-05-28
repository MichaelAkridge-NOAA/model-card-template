import requests
import os
from pathlib import Path

def download_model_images(repo_id: str, images_config: list, output_dir: str) -> dict:
    """Download images from Hugging Face repo and return local paths."""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    image_paths = {}
    base_url = f"https://huggingface.co/{repo_id}/resolve/main"
    
    for img_config in images_config:
        remote_path = img_config['path']
        local_filename = Path(remote_path).name
        local_path = os.path.join(output_dir, local_filename)
        
        # Download the image
        response = requests.get(f"{base_url}/{remote_path}", stream=True)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            image_paths[img_config['name']] = local_path
            
    return image_paths
