import json
from pathlib import Path

SOURCE = Path("projects.json")
CATALOGUE = Path("catalogue.json")
INDEX = Path("index.json")

# Read all imported SwitchPorts projects
with SOURCE.open("r", encoding="utf-8") as file:
    projects = json.load(file)

# Keep every project in the browsing catalogue
catalogue = {
    "schema": 1,
    "name": "SwitchPorts-tico",
    "description": "Browse active Nintendo Switch ports and homebrew projects.",
    "projects": projects
}

with CATALOGUE.open("w", encoding="utf-8") as file:
    json.dump(catalogue, file, indent=2, ensure_ascii=False)

# Keep the tico Store manifest valid.
# Installable packages will be added after their downloads are verified.
index = {
    "schema": 1,
    "name": "SwitchPorts-tico",
    "description": "Nintendo Switch ports and homebrew projects.",
    "packages": []
}

with INDEX.open("w", encoding="utf-8") as file:
    json.dump(index, file, indent=2, ensure_ascii=False)

print(f"Catalogue created with {len(projects)} projects.")
print("Installable packages: 0 (awaiting verified downloads).")
