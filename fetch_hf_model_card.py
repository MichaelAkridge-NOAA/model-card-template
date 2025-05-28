import requests
import json
import sys
import os
import re
from urllib.parse import urlparse

def parse_metrics(text):
    """Extract metrics from model card text"""
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

def fetch_model_card(url_or_id):
    """Fetch model card data from Hugging Face API"""
    repo_id = extract_repo_id(url_or_id)
    
    # Fetch from API
    api_url = f"https://huggingface.co/api/models/{repo_id}"
    response = requests.get(api_url)
    if response.status_code != 200:
        print(f"Failed to fetch model card from {api_url}")
        sys.exit(1)
        
    data = response.json()
    
    # Get the raw model card text
    model_card_text = data.get("cardData", "")
    
    # Try to extract structured data
    sections = {
        "Overview": model_card_text,
        "Model Type": data.get("pipeline_tag", ""),
        "Task": data.get("task", ""),
        "License": data.get("license", ""),
        "Downloads": data.get("downloads", 0)
    }

    # Extract metrics
    metrics = parse_metrics(model_card_text)
    
    model_info = {
        "model_name": data.get("modelId", repo_id),
        "version": data.get("sha", "N/A"),
        "release_date": data.get("lastModified", "N/A"),
        "architecture": data.get("pipeline_tag", "N/A"),
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
    with open(output_path, "w") as f:
        json.dump(hf_data, f, indent=2)
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