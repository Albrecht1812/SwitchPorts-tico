import json
import re
import urllib.request
from html import unescape

SOURCE = (
    "https://raw.githubusercontent.com/"
    "robzilla10001/SwitchPorts/main/README.md"
)


def clean(text):
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*`~]", "", text)
    return unescape(text).strip()


def extract_links(text):
    links = []

    # Markdown links: [name](https://example.com)
    links += re.findall(
        r"\]\(\s*<?(https?://[^)\s>]+)",
        text,
        re.I
    )

    # HTML links: href="https://example.com"
    links += re.findall(
        r'href=["\'](https?://[^"\']+)["\']',
        text,
        re.I
    )

    # Direct URLs
    links += re.findall(
        r"https?://[^\s|<>\"')]+",
        text,
        re.I
    )

    result = []

    for link in links:
        link = unescape(link).rstrip(".,;")
        if link not in result:
            result.append(link)

    return result


def import_projects():

    request = urllib.request.Request(
        SOURCE,
        headers={
            "User-Agent": "SwitchPorts-tico"
        }
    )

    with urllib.request.urlopen(request) as response:
        readme = response.read().decode("utf-8")

    projects = []
    category = "Uncategorised"
    headers = []

    for line in readme.splitlines():

        # Detect platform headings
        heading = re.match(
            r"^#{2,4}\s+(.+)",
            line
        )

        if heading:
            category = clean(heading.group(1))
            headers = []
            continue

        if not line.strip().startswith("|"):
            continue

        cells = [
            cell.strip()
            for cell in line.strip().strip("|").split("|")
        ]

        if not cells:
            continue

        # Ignore table separators
        if all(
            re.fullmatch(r"[-:\s]+", cell)
            for cell in cells
        ):
            continue

        lowered = [
            re.sub(r"[^a-z0-9 ]", "", cell.lower())
            for cell in cells
        ]

        # Detect table headers
        if any(
            value in ("title", "game", "name")
            for value in lowered
        ):
            headers = lowered
            continue

        if not headers:
            continue

        def get_column(*names):
            for name in names:
                if name in headers:
                    index = headers.index(name)

                    if index < len(cells):
                        return cells[index]

            return ""

        name_cell = get_column(
            "title",
            "game",
            "name"
        )

        name = clean(name_cell)

        if not name:
            continue

        if name.lower() in (
            "title",
            "game",
            "name"
        ):
            continue

        # Extract links from the entire row
        links = extract_links(line)

        # Prefer GitHub project links
        project_url = next(
            (
                url for url in links
                if "github.com" in url.lower()
            ),
            ""
        )

        # Fall back to another project link
        if not project_url:
            project_url = next(
                (
                    url for url in links
                    if "gbatemp.net" not in url.lower()
                ),
                ""
            )

        discussion_url = next(
            (
                url for url in links
                if "gbatemp.net" in url.lower()
            ),
            ""
        )

        version = clean(
            get_column("version")
        )

        updated = clean(
            get_column(
                "last updated",
                "updated"
            )
        )

        status = clean(
            get_column("status")
        )

        projects.append({
            "name": name,
            "category": category,
            "version": version,
            "last_updated": updated,
            "status": status,
            "project_url": project_url,
            "discussion_url": discussion_url,
            "source": SOURCE
        })

    # Remove duplicate entries
    unique = {}

    for project in projects:
        key = (
            project["category"],
            project["name"]
        )

        unique[key] = project

    projects = sorted(
        unique.values(),
        key=lambda p: (
            p["category"].lower(),
            p["name"].lower()
        )
    )

    # Save catalogue
    with open(
        "projects.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            projects,
            file,
            indent=2,
            ensure_ascii=False
        )

    linked = sum(
        1 for project in projects
        if project["project_url"]
    )

    discussions = sum(
        1 for project in projects
        if project["discussion_url"]
    )

    print("--------------------------------")
    print("SWITCHPORTS IMPORT RESULTS")
    print("--------------------------------")
    print(f"Imported projects: {len(projects)}")
    print(f"Projects with links: {linked}")
    print(f"Discussion links: {discussions}")
    print("--------------------------------")


if __name__ == "__main__":
    import_projects()
