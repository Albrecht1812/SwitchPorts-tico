import json
import os
import re
import urllib.request
import urllib.error
from pathlib import Path

SOURCE = Path("projects.json")
CATALOGUE = Path("catalogue.json")
INDEX = Path("index.json")

GITHUB_API = "https://api.github.com"

TOKEN = os.environ.get("GITHUB_TOKEN", "")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "SwitchPorts-tico-Catalogue"
}

if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def read_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def github_repository(url):
    if not url:
        return None

    match = re.search(
        r"github\.com/([^/]+)/([^/#?]+)",
        url
    )

    if not match:
        return None

    owner = match.group(1)
    repo = match.group(2).removesuffix(".git")

    return owner, repo


def get_latest_release(owner, repo):
    url = f"{GITHUB_API}/repos/{owner}/{repo}/releases/latest"

    request = urllib.request.Request(
        url,
        headers=HEADERS
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            release = json.loads(response.read().decode("utf-8"))

        assets = []

        for asset in release.get("assets", []):
            filename = asset.get("name", "")
            extension = Path(filename).suffix.lower()

            assets.append({
                "filename": filename,
                "download_url": asset.get("browser_download_url"),
                "size": asset.get("size", 0),
                "downloads": asset.get("download_count", 0),
                "type": extension
            })

        return {
            "version": release.get("tag_name", ""),
            "release_name": release.get("name", ""),
            "release_url": release.get("html_url", ""),
            "published_at": release.get("published_at", ""),
            "assets": assets
        }

    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None

        print(f"GitHub error for {owner}/{repo}: {error.code}")
        return None

    except Exception as error:
        print(f"Error checking {owner}/{repo}: {error}")
        return None


def main():
    projects = read_json(SOURCE)

    if isinstance(projects, dict):
        projects = projects.get("projects", [])

    total = len(projects)
    checked = 0
    releases_found = 0
    downloadable = 0

    print("Starting SwitchPorts release scanner...")
    print(f"Projects to check: {total}")

    for project in projects:
        repository = github_repository(
            project.get("project_url", "")
        )

        project["latest_release"] = None
        project["release_assets"] = []

        if not repository:
            continue

        owner, repo = repository

        release = get_latest_release(owner, repo)

        checked += 1

        if release:
            releases_found += 1

            project["latest_release"] = {
                "version": release["version"],
                "name": release["release_name"],
                "url": release["release_url"],
                "published_at": release["published_at"]
            }

            project["release_assets"] = release["assets"]

            if release["assets"]:
                downloadable += 1

        if checked % 25 == 0:
            print(f"Checked {checked}/{total} projects")

    catalogue = {
        "schema": 1,
        "name": "SwitchPorts-tico",
        "description": (
            "Browse active Nintendo Switch ports and "
            "homebrew projects, including their latest releases."
        ),
        "projects": projects
    }

    save_json(CATALOGUE, catalogue)

    # Do not automatically redistribute unverified binaries.
    # Installable packages will be generated once their
    # release format and redistribution conditions are verified.

    index = {
        "schema": 1,
        "name": "SwitchPorts-tico",
        "description": "Nintendo Switch ports and homebrew projects.",
        "packages": []
    }

    save_json(INDEX, index)

    print("--------------------------------")
    print("SWITCHPORTS SCAN RESULTS")
    print("--------------------------------")
    print(f"Projects checked: {checked}")
    print(f"Releases found: {releases_found}")
    print(f"Projects with downloadable assets: {downloadable}")
    print(f"Total projects: {total}")
    print("--------------------------------")
    print("Catalogue updated successfully.")


if __name__ == "__main__":
    main()
