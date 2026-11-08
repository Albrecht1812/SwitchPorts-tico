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
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[*`~]", "", text)
    return unescape(text).strip()

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
            for cell in line.strip("|").split("|")
        ]

        if not cells:
            continue

        if all(
            re.fullmatch(r"[-:\s]+", cell)
            for cell in cells
        ):
            continue

        lowered = [cell.lower() for cell in cells]

        if "version" in lowered and (
            "title" in lowered or "game" in lowered
        ):
            headers = lowered
            continue

        if not headers:
            continue

        name_index = next(
            (i for i, value in enumerate(headers)
             if value in ("title", "game")),
            0
        )

        if name_index >= len(cells):
            continue

        name = clean(cells[name_index])

        if not name:
            continue

        links = re.findall(
            r"$begin:math:display$\[\^$end:math:display$]*\]$begin:math:text$\(https\?\:\/\/\[\^\)\]\+\)$end:math:text$",
            line
        )

        project_url = next(
            (url for url in links
             if "github.com" in url
             or "buildbot.libretro.com" in url),
            ""
        )

        if not project_url:
            project_url = links[0] if links else ""

        version = ""
        updated = ""

        if "version" in headers:
            i = headers.index("version")
            if i < len(cells):
                version = clean(cells[i])

        if "last updated?" in headers:
            i = headers.index("last updated?")
            if i < len(cells):
                updated = clean(cells[i])

        projects.append({
            "name": name,
            "category": category,
            "version": version,
            "last_updated": updated,
            "project_url": project_url,
            "source": SOURCE
        })

    projects.sort(
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

if __name__ == "__main__":
    import_projects()
