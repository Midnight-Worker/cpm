import json
import shutil
import tarfile
import tempfile
import urllib.request
import zipfile

from pathlib import Path


GITHUB_API = "https://api.github.com/repos/{repo}/releases/latest"


def github_request(url):
    return urllib.request.Request(
        url,
        headers={
            "User-Agent": "cpm",
            "Accept": "application/vnd.github+json"
        }
    )


def find_release_asset(package):
    repo = package["repo"]

    url = GITHUB_API.format(repo=repo)

    request = github_request(url)

    with urllib.request.urlopen(request) as response:
        release = json.load(response)

    required = [
        part.strip().lower()
        for part in package["asset_contains"].split(",")
        if part.strip()
    ]

    for asset in release["assets"]:
        name = asset["name"].lower()

        if all(part in name for part in required):
            return {
                "name": asset["name"],
                "url": asset["browser_download_url"]
            }

    raise RuntimeError(
        f"Kein passendes Release-Asset für {package['name']} gefunden."
    )


def download(url, target):
    request = github_request(url)

    with urllib.request.urlopen(request) as response:
        with open(target, "wb") as file:
            shutil.copyfileobj(response, file)


def extract_archive(archive, destination):
    name = archive.name.lower()

    if name.endswith(".tar.gz") or name.endswith(".tgz"):
        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(destination)

        return

    if name.endswith(".zip"):
        with zipfile.ZipFile(archive) as zip_file:
            zip_file.extractall(destination)

        return

    raise RuntimeError(
        f"Archivformat nicht unterstützt: {archive.name}"
    )


def find_directory(root, name):
    candidates = []

    for path in root.rglob(name):
        if path.is_dir() and path.name == name:
            candidates.append(path)

    if not candidates:
        return None

    candidates.sort(
        key=lambda path: len(path.parts)
    )

    return candidates[0]


def copy_directory(source, destination):
    destination.mkdir(
        parents=True,
        exist_ok=True
    )

    shutil.copytree(
        source,
        destination,
        dirs_exist_ok=True
    )


def install_package(package, project, status=None):
    name = package["name"]

    if status:
        status(f"Suche aktuellen {name}-Release ...")

    asset = find_release_asset(package)

    if status:
        status(f"Lade {asset['name']} ...")

    with tempfile.TemporaryDirectory() as temporary_directory:
        temp = Path(temporary_directory)

        archive = temp / asset["name"]
        extracted = temp / "extracted"

        extracted.mkdir()

        download(
            asset["url"],
            archive
        )

        if status:
            status(f"Entpacke {name} ...")

        extract_archive(
            archive,
            extracted
        )

        mappings = [
            (
                package["include_source"],
                package["include_target"]
            ),
            (
                package["lib_source"],
                package["lib_target"]
            ),
            (
                package["bin_source"],
                package["bin_target"]
            ),
        ]

        for source_name, target_name in mappings:
            if not source_name or not target_name:
                continue

            source = find_directory(
                extracted,
                source_name
            )

            if not source:
                raise RuntimeError(
                    f"Verzeichnis '{source_name}' "
                    f"für Paket '{name}' nicht gefunden."
                )

            target = project / target_name

            if status:
                status(
                    f"Kopiere {source_name} → {target_name}"
                )

            copy_directory(
                source,
                target
            )

    if status:
        status(f"{name} installiert.")
