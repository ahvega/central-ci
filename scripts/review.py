import os
import sys
import json
import requests
import google_antigravity as agy

def main():
    github_token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    
    if not all([github_token, repo, event_path]):
        print("Error: Missing required GitHub environment variables.")
        sys.exit(1)

    with open(event_path, "r") as f:
        event_data = json.load(f)
        
    pr_number = event_data.get("pull_request", {}).get("number")
    if not pr_number:
        print("Could not find PR number in event payload. Exiting.")
        sys.exit(0)

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3.diff"
    }

    print(f"Fetching diff for PR #{pr_number} in {repo}...")
    diff_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    response = requests.get(diff_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch PR diff: {response.status_code} {response.text}")
        sys.exit(1)
        
    pr_diff = response.text

    if not pr_diff.strip():
        print("PR diff is empty. Nothing to review.")
        sys.exit(0)

    print("Initializing Antigravity Agent...")
    agent = agy.Agent()

    guidelines_path = os.environ.get("STYLE_GUIDE_PATH", "docs/style_guide.md")
    team_guidelines = ""
    if os.path.exists(guidelines_path):
        with open(guidelines_path, "r") as f:
            team_guidelines = f.read()
    else:
        print(f"Warning: Guidelines file not found at {guidelines_path}")

    review_prompt = f"""
    You are an expert code reviewer. Please review the following Pull Request diff.
    
    Look for:
    - Logic bugs or edge cases
    - Security vulnerabilities
    - Performance bottlenecks
    
    CRITICAL: You must strictly evaluate the code against our team's internal style guide provided below. 
    If the code violates any of these specific rules, flag it prominently in your review.
    
    
    {team_guidelines}
    
    
    Provide your feedback clearly and concisely in Markdown. Focus only on the changed lines.
    If the code looks perfect and follows all guidelines, simply reply: "LGTM! (Looks Good To Me) No issues found."
    
    Here is the diff: