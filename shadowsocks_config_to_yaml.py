#!/usr/bin/env python3
"""
Shadowsocks Config to YAML Converter

This program takes a Shadowsocks config file and creates individual YAML files
for each access key. Each YAML file is named after the password/secret and
contains the transport and reporter configuration.
"""

import json
import yaml
import argparse
import os
import sys
from typing import Dict, List, Any


def load_shadowsocks_config(config_file: str) -> Dict[str, Any]:
    """Load and parse the Shadowsocks config file."""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Config file '{config_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config file '{config_file}': {e}")
        sys.exit(1)


def generate_yaml_config(access_key: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
    """Generate YAML configuration for a single access key."""
    # Extract the base endpoint (remove port if present)
    base_endpoint = endpoint.split(':')[0] if ':' in endpoint else endpoint
    full_endpoint = f"{base_endpoint}:{access_key['port']}"
    
    # Generate prefix - use metricsId if available, otherwise use id or password prefix
    if 'metricsId' in access_key:
        prefix_id = access_key['metricsId'][:8]
    else:
        # Fallback to using the access key id or first 8 chars of password
        prefix_id = access_key.get('id', access_key['password'][:8])
    
    yaml_config = {
        'transport': {
            '$type': 'tcpudp',
            'tcp': {
                '$type': 'shadowsocks',
                'endpoint': full_endpoint,
                'cipher': access_key['encryptionMethod'],
                'secret': access_key['password'],
                'prefix': f"POST%20{prefix_id}"
            },
            'udp': '*shared'
        },
        'reporter': {
            '$type': 'http',
            'request': {
                'url': 'http://namaz-sw.qawqa.link:8080/health'
            },
            'interval': '24h',
            'enable_cookies': True
        }
    }
    
    # Add the shared reference anchor to tcp
    yaml_config['transport']['tcp'] = {
        **yaml_config['transport']['tcp']
    }
    
    return yaml_config


def create_yaml_files(config: Dict[str, Any], endpoint: str, output_dir: str = "."):
    """Create YAML files for each access key in the config."""
    access_keys = config.get('accessKeys', [])
    
    if not access_keys:
        print("No access keys found in the config file.")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    created_files = []
    
    for key in access_keys:
        # Generate YAML config
        yaml_config = generate_yaml_config(key, endpoint)
        
        # Use password as filename (no extension)
        filename = key['password']
        filepath = os.path.join(output_dir, filename)
        
        try:
            # Custom YAML dumper to handle the anchor reference
            yaml_content = create_yaml_with_anchor(yaml_config)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            
            created_files.append(filepath)
            print(f"Created: {filepath} (Key ID: {key['id']}, Name: {key['name']})")
            
        except IOError as e:
            print(f"Error creating file '{filepath}': {e}")
    
    print(f"\nTotal files created: {len(created_files)}")


def create_yaml_with_anchor(config: Dict[str, Any]) -> str:
    """Create YAML content with proper anchor and alias formatting."""
    yaml_lines = []
    yaml_lines.append("transport:")
    yaml_lines.append("  $type: tcpudp")
    yaml_lines.append("  tcp: &shared")
    yaml_lines.append("    $type: shadowsocks")
    yaml_lines.append(f"    endpoint: {config['transport']['tcp']['endpoint']}")
    yaml_lines.append(f"    cipher: {config['transport']['tcp']['cipher']}")
    yaml_lines.append(f"    secret: {config['transport']['tcp']['secret']}")
    yaml_lines.append(f"    prefix: {config['transport']['tcp']['prefix']}")
    yaml_lines.append("  udp: *shared")
    yaml_lines.append("reporter:")
    yaml_lines.append("  $type: http")
    yaml_lines.append("  request:")
    yaml_lines.append(f"    url: {config['reporter']['request']['url']}")
    yaml_lines.append(f"  interval: {config['reporter']['interval']}")
    yaml_lines.append(f"  enable_cookies: {str(config['reporter']['enable_cookies']).lower()}")
    
    return "\n".join(yaml_lines) + "\n"


def main():
    """Main function to handle command line arguments and orchestrate the conversion."""
    parser = argparse.ArgumentParser(
        description="Convert Shadowsocks config file to individual YAML files"
    )
    parser.add_argument(
        "config_file",
        help="Path to the Shadowsocks config JSON file"
    )
    parser.add_argument(
        "endpoint",
        help="Base endpoint (e.g., c1.nastuh.link or c1.nastuh.link:443)"
    )
    parser.add_argument(
        "-o", "--output",
        default=".",
        help="Output directory for YAML files (default: current directory)"
    )
    
    args = parser.parse_args()
    
    # Load the config file
    config = load_shadowsocks_config(args.config_file)
    
    # Create YAML files
    create_yaml_files(config, args.endpoint, args.output)


if __name__ == "__main__":
    main()