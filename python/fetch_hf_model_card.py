import requests
from bs4 import BeautifulSoup
import json
import re

def fetch_huggingface_model_card(repo_id):
    """Fetch model card content from Hugging Face."""
    
    url = f"https://huggingface.co/{repo_id}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch model card. Status code: {response.status_code}")
    
    # Parse the HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the model card content
    article = soup.find('article', class_='prose')
    if not article:
        raise Exception("Could not find model card content")
    
    # Extract sections
    sections = {}
    current_section = "Overview"
    current_content = []
    
    for element in article.children:
        if element.name == 'h2':
            # Save previous section
            if current_content:
                sections[current_section] = '\n'.join(current_content)
            # Start new section
            current_section = element.get_text()
            current_content = []
        else:
            if element.name:  # Skip empty text nodes
                current_content.append(str(element))
    
    # Save last section
    if current_content:
        sections[current_section] = '\n'.join(current_content)
    
    # Extract model info
    model_info = {
        "model_name": repo_id.split('/')[-1],
        "author": repo_id.split('/')[0],
        "likes": soup.find('button', {'aria-label': re.compile(r'Like .* times')})['aria-label'].split()[1],
        "downloads": soup.find('button', {'aria-label': re.compile(r'Download .* times')})['aria-label'].split()[1]
    }
    
    return {
        "model_info": model_info,
        "sections": sections
    }

if __name__ == "__main__":
    model_data = fetch_huggingface_model_card("akridge/yolo11-fish-detector-grayscale")
    print(json.dumps(model_data, indent=2))
