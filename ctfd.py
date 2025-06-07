import os
import requests
import yaml
from urllib.parse import urljoin
from datetime import datetime
import argparse


class CTFdConfig:
    @staticmethod
    def load_config(ctf_dir):
        config_path = os.path.join(ctf_dir, '.ctfd.yaml')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    if config.get('platform') == 'CTFd':
                        return config
                    print("Warning: Config file exists but is not a valid CTFd config")
            except Exception as e:
                print(f"Warning: Could not read config file: {e}")
        return None

    @staticmethod
    def create_config(base_url, ctf_dir):
        config = {
            'platform': 'CTFd',
            'url': base_url,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'version': 1
        }
        
        config_path = os.path.join(ctf_dir, '.ctfd.yaml')
        try:
            with open(config_path, 'w') as f:
                yaml.dump(config, f, sort_keys=False)
            print(f"Created CTFd config file: {config_path}")
            return config
        except Exception as e:
            print(f"Warning: Could not create config file: {e}")
            return None

    @staticmethod
    def update_config(ctf_dir, new_data):
        config_path = os.path.join(ctf_dir, '.ctfd.yaml')
        try:
            # Read existing config
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            
            # Update with new data
            config.update(new_data)
            config['updated_at'] = datetime.now().isoformat()
            
            # Write back
            with open(config_path, 'w') as f:
                yaml.dump(config, f, sort_keys=False)
            return True
        except Exception as e:
            print(f"Warning: Could not update config file: {e}")
            return False


def ensure_directory_exists(path):
    """Ensure directory exists, create if it doesn't, and verify write permissions"""
    try:
        os.makedirs(path, exist_ok=True)
        test_file = os.path.join(path, '.permission_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        return True
    except OSError as e:
        print(f"Error: Cannot create or write to directory '{path}': {e}")
        return False


def fetch_challenges(base_url, api_token):
    """Fetch challenges from CTFd API"""
    headers = {
        "Authorization": f"Token {api_token}",
        "Content-Type": "application/json"
    }
    challenges_url = urljoin(base_url, "/api/v1/challenges")

    try:
        response = requests.get(challenges_url, headers=headers)
        response.raise_for_status()
        return response.json().get('data', [])
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch challenges: {e}")


def fetch_challenge_details(base_url, api_token, challenge_id):
    """Fetch detailed information for a specific challenge"""
    headers = {
        "Authorization": f"Token {api_token}",
        "Content-Type": "application/json"
    }
    challenge_url = urljoin(base_url, f"/api/v1/challenges/{challenge_id}")

    try:
        response = requests.get(challenge_url, headers=headers)
        response.raise_for_status()
        return response.json().get('data', {})
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch challenge details for challenge {challenge_id}: {e}")


def download_challenge_files(base_url, api_token, challenge_id, download_dir):
    """Download files associated with a challenge"""
    headers = {
        "Authorization": f"Token {api_token}",
    }
    
    details = fetch_challenge_details(base_url, api_token, challenge_id)
    if not details or not details.get('files'):
        return False
        
    if not ensure_directory_exists(download_dir):
        return False
    
    downloaded_files = []
    for file_url in details['files']:
        try:
            if not file_url.startswith('http'):
                file_url = urljoin(base_url, file_url)
            
            file_name = os.path.basename(file_url.split('?')[0])
            file_path = os.path.join(download_dir, file_name)
            
            with requests.get(file_url, headers=headers, stream=True) as r:
                r.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            downloaded_files.append(file_name)
        except requests.exceptions.RequestException as e:
            print(f"Warning: Failed to download file {file_url}: {e}")
            
    return bool(downloaded_files)


def organize_challenges_by_category(challenges):
    """Organize challenges into categories with their IDs"""
    categories = {}
    for challenge in challenges:
        category = challenge.get('category')
        name = challenge.get('name')
        challenge_id = challenge.get('id')
        if not all([category, name, challenge_id]):
            continue

        if category not in categories:
            categories[category] = []
        categories[category].append((name, challenge_id))
    return categories


def create_challenge_directories(root_dir, categories, base_url, api_token):
    """Create directory structure for challenges and add README files"""
    for category, challenges in categories.items():
        category_dir = os.path.join(root_dir, sanitize_name(category))
        if not ensure_directory_exists(category_dir):
            continue

        for name, challenge_id in challenges:
            challenge_dir = os.path.join(category_dir, sanitize_name(name))
            if not ensure_directory_exists(challenge_dir):
                continue
            
            create_readme(challenge_dir, base_url, api_token, challenge_id, name)
            if not download_challenge_files(base_url, api_token, challenge_id, challenge_dir):
                print(f"No files downloaded for challenge {name} (ID: {challenge_id})")


def create_readme(challenge_dir, base_url, api_token, challenge_id, challenge_name):
    """Create a README.md file with challenge description"""
    try:
        details = fetch_challenge_details(base_url, api_token, challenge_id)
        if not details:
            return
            
        with open(os.path.join(challenge_dir, "README.md"), 'w', encoding='utf-8') as f:
            f.write(f"# {challenge_name}\n\n{details.get('description', 'No description provided')}\n\n")
            f.write("## Challenge Details\n")
            f.write(f"- ID: {challenge_id}\n")
            f.write(f"- Category: {details.get('category', 'N/A')}\n")
            f.write(f"- Value: {details.get('value', 'N/A')} points\n")
            if details.get('tags'):
                f.write(f"- Tags: {', '.join(tag['value'] for tag in details['tags'])}\n")
            if details.get('files'):
                f.write("\n## Files\n")
                for file_url in details['files']:
                    f.write(f"- `{os.path.basename(file_url.split('?')[0])}`\n")
    except Exception as e:
        print(f"Warning: Could not create README for {challenge_name}: {e}")


def sanitize_name(name):
    """Sanitize directory names by replacing problematic characters"""
    return "".join(c if c.isalnum() or c in (' ', '-', '_') else '_'
                 for c in name).strip().replace(" ", "_")


def run_from_config(ctf_dir, api_token):
    """Run using existing config file"""
    config = CTFdConfig.load_config(ctf_dir)
    if not config:
        raise Exception("No valid CTFd config found")
    
    print(f"Using CTFd instance: {config['url']}")
    challenges = fetch_challenges(config['url'], api_token)
    if not challenges:
        print("No challenges found!")
        return
    
    categories = organize_challenges_by_category(challenges)
    create_challenge_directories(ctf_dir, categories, config['url'], api_token)
    CTFdConfig.update_config(ctf_dir, {'last_sync': datetime.now().isoformat()})


def run_with_new_config(base_url, api_token, ctf_dir):
    """Run with new configuration"""
    if not ensure_directory_exists(ctf_dir):
        raise Exception(f"Cannot create or write to directory: {ctf_dir}")
    
    CTFdConfig.create_config(base_url, ctf_dir)
    challenges = fetch_challenges(base_url, api_token)
    if not challenges:
        print("No challenges found!")
        return
    
    categories = organize_challenges_by_category(challenges)
    create_challenge_directories(ctf_dir, categories, base_url, api_token)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CTF Challenge Directory Manager")
    parser.add_argument("-d", "--directory", required=True, help="Path to CTF directory")
    parser.add_argument("-t", "--token", required=True, help="API token for authentication")
    parser.add_argument("-u", "--url", help="Base URL of CTFd instance (required for new config)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()

    try:
        if args.url:
            # Create new config or overwrite existing
            run_with_new_config(args.url, args.token, args.directory)
        else:
            # Use existing config
            run_from_config(args.directory, args.token)
        
        print(f"\nOperation completed in: {os.path.abspath(args.directory)}")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
