import json
import re
import urllib.request
from html import unescape

SOURCE = (
    "https://raw.githubusercontent.com/"
    "robzilla10001/SwitchPorts/main/README.md"
)

def clean(text):
    text = re.sub(r"<br\s*/?>", " ", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*`~]", "", text)
    return unescape(text).strip()

def get_links(text):
    return re.findall(
        r"\]$begin:math:text$\(https\?\:\/\/\[\^\)\\s\]\+\)$end:math:text$",
        text
    )

def import_projects():
    request = urllib.request.Request(
        SOURCE,
        headers={"User-Agent": "SwitchPorts-tico"}
    )

    with urllib.request.urlopen(request) as response:
        readme = response.read().decode("utf-8")

    projects = []
    category = "Uncategorised"
    headers = []

    for line in readme.splitlines():

        heading = re.match(r"^###\s+(.+)", line)

        if heading:
            category = clean(heading.group(1))
            headers = []
            continue

        if not line.startswith("|"):
            continue

        cells = [
            cell.strip()
            for cell in line.strip().strip("|").split("|")
        ]

        if not cells:
            continue

        if all(re.fullmatch(r"[-:\s]+", c) for c in cells):
            continue

        lowered = [c.lower().strip("?") for c in cells]

        if any(x in lowered for x in ["title", "game"]):
            headers = lowered
            continue

        if not headers:
            continue

        def get_column(*names):
            for name in names:
                if name in headers:
                    i = headers.index(name)
                    if i < len(cells):
                        return cells[i]
            return ""

        name_cell = get_column("title", "game")

        name = clean(name_cell)

        if not name or name.lower() in ["title", "game"]:
            continue

        links = get_links(line)

        project_url = ""
        discussion_url = ""

        link_cell = get_column("link")

        if link_cell:
            cell_links = get_links(link_cell)
            if cell_links:
                project_url = cell_links[0]

        discussion_cell = get_column("gbatemp thread")

        if discussion_cell:
            discussion_links = get_links(discussion_cell)
            if discussion_links:
                discussion_url = discussion_links[0]

        version = clean(get_column("version"))
        updated = clean(get_column("last updated"))
        status = clean(get_column("status"))

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

    unique = {}
    for project in projects:
        key = (project["category"], project["name"])
        unique[key] = project

    projects = sorted(
        unique.values(),
        key=lambda p: (
            p["category"].lower(),
            p["name"].lower()
        )
    )

    with open("projects.json", "w", encoding="utf-8") as file:
        json.dump(
            projects,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(f"Imported {len(projects)} projects.")

    linked = sum(
        1 for p in projects if p["project_url"]
    )

    print(f"Projects with links: {linked}")

if __name__ == "__main__":
    import_projects()
