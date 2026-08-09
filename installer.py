import json
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
import zipfile

from pathlib import Path


GITHUB_API = "https://api.github.com/repos/{repo}/releases/latest"

SDL2_VERSION = "2.32.10"
SDL2_URL = (
    f"https://libsdl.org/release/"
    f"SDL2-{SDL2_VERSION}.tar.gz"
)


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
        f"Kein passendes Release-Asset für "
        f"{package['name']} gefunden."
    )


def download(url, target):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "cpm"
        }
    )

    with urllib.request.urlopen(request) as response:
        with open(target, "wb") as file:
            shutil.copyfileobj(
                response,
                file
            )


def extract_archive(archive, destination):
    name = archive.name.lower()

    if name.endswith(".tar.gz") or name.endswith(".tgz"):
        with tarfile.open(
            archive,
            "r:gz"
        ) as tar:
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


def run(command, cwd=None):
    subprocess.run(
        command,
        cwd=cwd,
        check=True
    )


def install_sdl2(package, project, status=None):
    if status:
        status(
            f"Lade SDL2 {SDL2_VERSION} ..."
        )

    with tempfile.TemporaryDirectory() as temp_directory:
        temp = Path(temp_directory)

        archive = temp / f"SDL2-{SDL2_VERSION}.tar.gz"
        extracted = temp / "source"

        extracted.mkdir()

        download(
            SDL2_URL,
            archive
        )

        if status:
            status("Entpacke SDL2 ...")

        extract_archive(
            archive,
            extracted
        )

        source = (
            extracted
            / f"SDL2-{SDL2_VERSION}"
        )

        if not source.exists():
            raise RuntimeError(
                "SDL2 Quellverzeichnis wurde nicht gefunden."
            )

        build = temp / "build"
        install = temp / "install"

        build.mkdir()
        install.mkdir()

        if status:
            status("Konfiguriere SDL2 ...")

        configure = source / "configure"

        if not configure.exists():
            raise RuntimeError(
                "SDL2 configure-Script fehlt."
            )

        run(
            [
                str(configure),
                f"--prefix={install}",
                "--disable-shared",
                "--enable-static"
            ],
            cwd=build
        )

        if status:
            status("Baue SDL2 ...")

        run(
            [
                "make",
                "-j2"
            ],
            cwd=build
        )

        if status:
            status("Installiere SDL2 lokal ...")

        run(
            [
                "make",
                "install"
            ],
            cwd=build
        )

        include_source = (
            install
            / "include"
            / "SDL2"
        )

        lib_source = (
            install
            / "lib"
        )

        include_target = (
            project
            / "vendor"
            / "sdl2"
            / "include"
            / "SDL2"
        )

        lib_target = (
            project
            / "vendor"
            / "sdl2"
            / "lib"
        )

        if status:
            status("Kopiere SDL2 Header ...")

        copy_directory(
            include_source,
            include_target
        )

        if status:
            status("Kopiere SDL2 Bibliothek ...")

        lib_target.mkdir(
            parents=True,
            exist_ok=True
        )

        static_lib = (
            lib_source
            / "libSDL2.a"
        )

        if not static_lib.exists():
            raise RuntimeError(
                "libSDL2.a wurde nicht erzeugt."
            )

        shutil.copy2(
            static_lib,
            lib_target / "libSDL2.a"
        )

    if status:
        status("SDL2 installiert.")


def install_generic(
    package,
    project,
    status=None
):
    name = package["name"]

    if status:
        status(
            f"Suche aktuellen {name}-Release ..."
        )

    asset = find_release_asset(
        package
    )

    if status:
        status(
            f"Lade {asset['name']} ..."
        )

    with tempfile.TemporaryDirectory() as temp_directory:
        temp = Path(temp_directory)

        archive = temp / asset["name"]
        extracted = temp / "extracted"

        extracted.mkdir()

        download(
            asset["url"],
            archive
        )

        if status:
            status(
                f"Entpacke {name} ..."
            )

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
                    f"für Paket '{name}' "
                    f"nicht gefunden."
                )

            target = (
                project
                / target_name
            )

            if status:
                status(
                    f"Kopiere "
                    f"{source_name} "
                    f"→ {target_name}"
                )

            copy_directory(
                source,
                target
            )

    if status:
        status(
            f"{name} installiert."
        )


def install_package(
    package,
    project,
    status=None
):
    package_type = (
        package["package_type"]
        or "generic"
    )

    if package_type == "sdl2":
        install_sdl2(
            package,
            project,
            status
        )

        return

    install_generic(
        package,
        project,
        status
    )
