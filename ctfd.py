import os
import requests
from urllib.parse import urljoin


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


def organize_challenges_by_category(challenges):
    """Organize challenges into categories"""
    categories = {}
    for challenge in challenges:
        category = challenge.get('category')
        name = challenge.get('name')
        if not category or not name:
            continue
            
        if category not in categories:
            categories[category] = []
        categories[category].append(name)
    return categories


def create_challenge_directories(root_dir, categories):
    """Create directory structure for challenges"""
    for category, challenge_names in categories.items():
        category_dir = os.path.join(root_dir, sanitize_name(category))
        os.makedirs(category_dir, exist_ok=True)
        
        for name in challenge_names:
            challenge_dir = os.path.join(category_dir, sanitize_name(name))
            os.makedirs(challenge_dir, exist_ok=True)
            print(f"Created: {challenge_dir}")


def sanitize_name(name):
    """Sanitize directory names by replacing problematic characters"""
    return "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' 
                 for c in name).replace(" ", "_")


def create_ctf_directory_structure(base_url, api_token, ctf_dir):
    """Main function to create CTF directory structure"""
    try:
        # Fetch and process challenges
        challenges = fetch_challenges(base_url, api_token)
        if not challenges:
            print("No challenges found in the CTF!")
            return
            
        categories = organize_challenges_by_category(challenges)
        
        # Create directory structure
        os.makedirs(ctf_dir, exist_ok=True)
        create_challenge_directories(ctf_dir, categories)
        
        print(f"\nSuccessfully created directory structure at: {os.path.abspath(ctf_dir)}")
    except Exception as e:
        print(f"Error: {e}")



if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CTF Challenge Directory Structure Creator")
    parser.add_argument("-d", "--directory", required=True, help="Path to CTF directory")
    parser.add_argument("-u", "--url", required=True, help="Base URL of CTFd instance")
    parser.add_argument("-t", "--token", required=True, help="API token for authentication")
    
    args = parser.parse_args()
    
    create_ctf_directory_structure(
        base_url=args.url,
        api_token=args.token,
        ctf_dir=args.directory
    )
