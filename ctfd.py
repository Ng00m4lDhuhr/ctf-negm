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
        raise Exception(f"Failed to fetch challenge details: {e}")


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
        os.makedirs(category_dir, exist_ok=True)

        for name, challenge_id in challenges:
            challenge_dir = os.path.join(category_dir, sanitize_name(name))
            os.makedirs(challenge_dir, exist_ok=True)
            
            # Create README.md with challenge description
            create_readme(challenge_dir, base_url, api_token, challenge_id, name)
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
            f.write(f"- Category: {details.get('category', 'N/A')}\n")
            f.write(f"- Value: {details.get('value', 'N/A')} points\n")
            if 'tags' in details and details['tags']:
                f.write(f"- Tags: {', '.join(tag['value'] for tag in details['tags'])}\n")
    except Exception as e:
        print(f"Warning: Could not create README for {challenge_name}: {e}")


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
        create_challenge_directories(ctf_dir, categories, base_url, api_token)

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
