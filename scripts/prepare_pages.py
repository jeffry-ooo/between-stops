"""Package the existing public spike for Pages without downloading feeds."""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "site"
OUTPUT = ROOT / "_site"
PUBLIC_FILES = (
    "index.html", "city.html", "about.html", "support.html", "contact.html",
    "styles.css", "app.js", "gallery.js", "cities.json",
)


def main():
    manifest = json.loads((SOURCE / "cities.json").read_text())
    files = list(PUBLIC_FILES)
    for city in manifest:
        if city.get("status") != "live":
            continue
        name = city["file"]
        if Path(name).name != name or not name.endswith(".json"):
            raise ValueError(f"Unexpected route filename: {name}")
        data = json.loads((SOURCE / name).read_text())
        if not data.get("loops"):
            raise ValueError(f"No routes in {name}")
        files.append(name)
    # Validate before replacing the local build directory.
    for name in files:
        if not (SOURCE / name).is_file():
            raise FileNotFoundError(name)
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir()
    for name in files:
        shutil.copy2(SOURCE / name, OUTPUT / name)
    (OUTPUT / ".nojekyll").touch()
    print(f"Prepared {len(files)} public files in {OUTPUT}")


if __name__ == "__main__":
    main()
