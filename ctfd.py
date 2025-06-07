import os
import requests
from urllib.parse import urljoin
import json


def ensure_directory_exists(path):
    """Ensure directory exists, create if it doesn't, and verify write permissions"""
    try:
        os.makedirs(path, exist_ok=True)
        # Verify we can write to the directory by creating a test file
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
    
    # First check if there are any files in the challenge details
    details = fetch_challenge_details(base_url, api_token, challenge_id)
    if not details or not details.get('files'):
        return False
        
    files = details['files']
    if not files:
        return False
        
    if not ensure_directory_exists(download_dir):
        return False
    
    downloaded_files = []
    
    for file_url in files:
        try:
            # Handle relative URLs
            if not file_url.startswith('http'):
                file_url = urljoin(base_url, file_url)
            
            file_name = os.path.basename(file_url.split('?')[0])  # Remove query params
            file_path = os.path.join(download_dir, file_name)
            
            print(f"Attempting to download {file_url} to {file_path}")
            
            with requests.get(file_url, headers=headers, stream=True) as r:
                r.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            downloaded_files.append(file_name)
            print(f"Successfully downloaded: {file_name}")
            
        except requests.exceptions.RequestException as e:
            print(f"Warning: Failed to download file {file_url}: {e}")
            continue
            
    return bool(downloaded_files)


def organize_challenges_by_category(challenges):
    """Organize challenges into categories with their IDs"""
    categories = {}
    for challenge in challenges:
        category = challenge.get('category')
        name = challenge.get('name')
        challenge_id = challenge.get('id')
        if not category or not name or not challenge_id:
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
            
            # Create README.md with challenge description
            create_readme(challenge_dir, base_url, api_token, challenge_id, name)
            
            # Download challenge files
            if not download_challenge_files(base_url, api_token, challenge_id, challenge_dir):
                print(f"No files downloaded for challenge {name} (ID: {challenge_id})")
            
            print(f"Created: {challenge_dir}")


def create_readme(challenge_dir, base_url, api_token, challenge_id, challenge_name):
    """Create a README.md file with challenge description"""
    try:
        details = fetch_challenge_details(base_url, api_token, challenge_id)
        if not details:
            return
            
        description = details.get('description', 'No description provided')
        readme_path = os.path.join(challenge_dir, "README.md")
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(f"# {challenge_name}\n\n")
            f.write(f"{description}\n\n")
            f.write("## Challenge Details\n")
            f.write(f"- ID: {challenge_id}\n")
            f.write(f"- Category: {details.get('category', 'N/A')}\n")
            f.write(f"- Value: {details.get('value', 'N/A')} points\n")
            if 'tags' in details and details['tags']:
                f.write(f"- Tags: {', '.join(tag['value'] for tag in details['tags'])}\n")
            
            # List files if they exist
            if details.get('files'):
                f.write("\n## Files\n")
                for file_url in details['files']:
                    file_name = os.path.basename(file_url.split('?')[0])
                    f.write(f"- `{file_name}`\n")
    except Exception as e:
        print(f"Warning: Could not create README for {challenge_name}: {e}")


def sanitize_name(name):
    """Sanitize directory names by replacing problematic characters"""
    return "".join(c if c.isalnum() or c in (' ', '-', '_') else '_'
                 for c in name).strip().replace(" ", "_")


def create_ctf_directory_structure(base_url, api_token, ctf_dir):
    """Main function to create CTF directory structure"""
    try:
        print(f"Starting CTF directory creation at {ctf_dir}")
        print(f"Using API endpoint: {base_url}")
        
        # Verify we can create and write to the directory
        if not ensure_directory_exists(ctf_dir):
            raise Exception(f"Cannot create or write to directory: {ctf_dir}")
        
        # Fetch and process challenges
        print("Fetching challenges...")
        challenges = fetch_challenges(base_url, api_token)
        if not challenges:
            print("No challenges found in the CTF!")
            return

        print(f"Found {len(challenges)} challenges")
        categories = organize_challenges_by_category(challenges)
        print(f"Organized into {len(categories)} categories")

        # Create directory structure
        create_challenge_directories(ctf_dir, categories, base_url, api_token)

        print(f"\nSuccessfully created directory structure at: {os.path.abspath(ctf_dir)}")
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CTF Challenge Directory Structure Creator")
    parser.add_argument("-d", "--directory", required=True, help="Path to CTF directory (will be created if doesn't exist)")
    parser.add_argument("-u", "--url", required=True, help="Base URL of CTFd instance")
    parser.add_argument("-t", "--token", required=True, help="API token for authentication")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    try:
        create_ctf_directory_structure(
            base_url=args.url,
            api_token=args.token,
            ctf_dir=args.directory
        )
    except Exception as e:
        print(f"Fatal error: {e}")
        exit(1)
