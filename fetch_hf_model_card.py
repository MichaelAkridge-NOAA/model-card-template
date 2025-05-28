import requests
import json
import sys
import os
import re
from urllib.parse import urlparse
from datetime import datetime

def parse_metrics(text):
    """Extract metrics from model card text"""
    if text is None or not isinstance(text, str):
        return {}
        
    metrics = {
        'mAP': None,
        'Precision': None,
        'Recall': None,
    }
    # Common patterns for metrics
    patterns = {
        'mAP': r'mAP[@\s]*0\.5[\s:]+([0-9.]+)',
        'Precision': r'[Pp]recision[\s:]+([0-9.]+)',
        'Recall': r'[Rr]ecall[\s:]+([0-9.]+)'
    }
    for metric, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            metrics[metric] = float(match.group(1))
    return metrics

def extract_repo_id(url_or_id):
    """Extract repository ID from URL or direct input"""
    if url_or_id.startswith('http'):
        parsed = urlparse(url_or_id)
        path = parsed.path.strip('/')
        # Handle both huggingface.co/org/model and huggingface.co/models/org/model URLs
        parts = path.split('/')
        if 'models' in parts:
            idx = parts.index('models')
            return '/'.join(parts[idx+1:])
        return path
    return url_or_id

def fetch_readme_content(repo_id):
    """Fetch README.md content from the repository"""
    readme_url = f"https://huggingface.co/{repo_id}/raw/main/README.md"
    response = requests.get(readme_url)
    if response.status_code == 200:
        return response.text
    return None

def fetch_model_card(url_or_id):
    """Fetch model card data from Hugging Face API and Git repository"""
    repo_id = extract_repo_id(url_or_id)
    
    # Try to fetch from API first
    api_url = f"https://huggingface.co/api/models/{repo_id}"
    response = requests.get(api_url)
    if response.status_code != 200:
        print(f"Warning: Failed to fetch model card from API {api_url}")
        data = {}
    else:
        data = response.json()

    # Fetch README content from Git
    readme_content = fetch_readme_content(repo_id)
    
    # Combine data from both sources
    model_card_text = data.get("cardData", "") or readme_content or ""
    
    sections = {
        "Overview": model_card_text,
        "Model Type": data.get("pipeline_tag", ""),
        "Task": data.get("task", ""),
        "License": data.get("license", ""),
        "Downloads": data.get("downloads", 0)
    }

    # Extract metrics from both sources
    metrics = parse_metrics(model_card_text)
    
    # Get the last modified date
    last_modified = data.get("lastModified", datetime.now().isoformat())
    try:
        last_modified = datetime.fromisoformat(last_modified.replace('Z', '+00:00')).strftime('%Y-%m-%d')
    except (ValueError, AttributeError):
        last_modified = datetime.now().strftime('%Y-%m-%d')

    model_info = {
        "model_name": data.get("modelId", repo_id),
        "version": data.get("sha", "latest"),
        "release_date": last_modified,
        "architecture": data.get("pipeline_tag", ""),
        "input_size": data.get("config", {}).get("image_size", "N/A"),
        "training_data": sections.get("Training Data", "N/A"),
        "metrics": metrics
    }

    # Create final data structure
    hf_data = {
        "model_info": model_info,
        "sections": sections,
    }

    # Save to JSON
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "model_data.json")
    with open(output_path, "w", encoding='utf-8') as f:
        json.dump(hf_data, f, indent=2, ensure_ascii=False)
    print(f"Saved model data to {output_path}")
    return output_path

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python fetch_hf_model_card.py <url_or_repo_id>")
        print("Example URLs:")
        print("  https://huggingface.co/org/model")
        print("  https://huggingface.co/models/org/model")
        print("  org/model")
        sys.exit(1)
    fetch_model_card(sys.argv[1])