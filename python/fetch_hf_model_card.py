import requests
from bs4 import BeautifulSoup
import json
import re
import yaml
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ModelCardSection:
    name: str
    content: str
    required: bool = False

@dataclass
class ModelMetric:
    name: str
    value: float
    description: str

@dataclass
class ModelCardContent:
    repo_id: str
    model_name: str
    author: str
    sections: Dict[str, ModelCardSection]
    metrics: List[ModelMetric]
    metadata: dict
    images: Dict[str, str]
    likes: Optional[int] = None
    downloads: Optional[int] = None

def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def extract_markdown_content(repo_id: str) -> str:
    """Fetch README.md content directly from Hugging Face."""
    api_url = f"https://huggingface.co/{repo_id}/raw/main/README.md"
    response = requests.get(api_url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch README.md. Status code: {response.status_code}")
    return response.text

def extract_yaml_header(content: str) -> dict:
    """Extract YAML header from markdown content."""
    if content.startswith('---'):
        parts = content.split('---', 2)[1:]
        if len(parts) >= 1:
            try:
                return yaml.safe_load(parts[0])
            except yaml.YAMLError:
                return {}
    return {}

def extract_section(content: str, section_pattern: str) -> str:
    """Extract a section from markdown content using regex."""
    pattern = f"{section_pattern}.*?(?=##|$)"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(0).strip()
    return ""

def extract_metrics(content: str, metrics_config: List[dict]) -> List[ModelMetric]:
    """Extract metrics using patterns from config."""
    metrics = []
    for metric_config in metrics_config:
        pattern = metric_config['pattern']
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            metrics.append(ModelMetric(
                name=metric_config['name'],
                value=float(match.group(1)),
                description=metric_config['description']
            ))
    return metrics

def fetch_huggingface_model_card(repo_id: str, config_path: str) -> ModelCardContent:
    """Fetch and parse model card content using configuration."""
    
    # Load config
    config = load_config(config_path)
    
    # Fetch markdown content
    content = extract_markdown_content(repo_id)
    
    # Extract YAML header metadata
    metadata = extract_yaml_header(content)
    
    # Extract sections
    sections = {}
    for section_config in config['model_card']['sections_to_extract']:
        section_content = extract_section(content, section_config['pattern'])
        sections[section_config['name']] = ModelCardSection(
            name=section_config['name'],
            content=section_content,
            required=section_config.get('required', False)
        )
    
    # Extract metrics
    metrics = extract_metrics(content, config['model_card']['metrics_to_extract'])
    
    # Get model info
    model_name = repo_id.split('/')[-1]
    author = repo_id.split('/')[0]
    
    # Create images dict (we'll handle actual image downloading separately)
    images = {img['name']: img['path'] for img in config['model_card']['images_to_include']}
    
    return ModelCardContent(
        repo_id=repo_id,
        model_name=model_name,
        author=author,
        sections=sections,
        metrics=metrics,
        metadata=metadata,
        images=images
    )

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python fetch_hf_model_card.py <repo_id>")
        sys.exit(1)
    
    repo_id = sys.argv[1]
    model_data = fetch_huggingface_model_card(repo_id)
    
    # Save the data to a JSON file for build.py to use
    output_path = os.path.join(os.path.dirname(__file__), "model_data.json")
    with open(output_path, "w") as f:
        json.dump(model_data, indent=2, fp=f)
    
    print(f"Model data saved to: {output_path}")
