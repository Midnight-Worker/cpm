#!/usr/bin/env python3

import curses
import json
import os
import shutil
import tarfile
import tempfile
import urllib.request
from pathlib import Path


GITHUB_API = "https://api.github.com/repos/slint-ui/slint/releases/latest"


def status(stdscr, text):
    stdscr.clear()
    stdscr.addstr(1, 2, "CPM - C++ Package Manager")
    stdscr.addstr(3, 2, text)
    stdscr.refresh()


def download(url, target):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "cpm"}
    )

    with urllib.request.urlopen(request) as response:
        with open(target, "wb") as file:
            shutil.copyfileobj(response, file)


def find_slint_asset():
    request = urllib.request.Request(
        GITHUB_API,
        headers={
            "User-Agent": "cpm",
            "Accept": "application/vnd.github+json"
        }
    )

    with urllib.request.urlopen(request) as response:
        release = json.load(response)

    for asset in release["assets"]:
        name = asset["name"].lower()

        if (
            "cpp" in name
            and "linux" in name
            and "x86_64" in name
            and name.endswith(".tar.gz")
        ):
            return (
                asset["name"],
                asset["browser_download_url"]
            )

    raise RuntimeError("Kein passendes Slint C++ SDK gefunden.")


def find_directory(root, name):
    for path in root.rglob(name):
        if path.is_dir():
            return path

    return None


def copy_directory(source, target):
    target.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        source,
        target,
        dirs_exist_ok=True
    )


def create_main_cpp(project):
    file = project / "main.cpp"

    if file.exists():
        return

    file.write_text(
'''#include "ui.h"

int main()
{
    auto app = App::create();
    app->run();

    return 0;
}
'''
    )


def create_ui(project):
    file = project / "ui.slint"

    if file.exists():
        return

    file.write_text(
'''export component App inherits Window {
    width: 400px;
    height: 240px;
    title: "CPM Slint";

    Text {
        text: "Hallo aus C++!";
        font-size: 28px;
        horizontal-alignment: center;
        vertical-alignment: center;
    }
}
'''
    )


def create_makefile(project):
    file = project / "Makefile"

    if file.exists():
        return

    file.write_text(
'''CXX := g++

SLINT := vendor/slint
SLINT_COMPILER := $(SLINT)/bin/slint-compiler

CXXFLAGS := -std=c++20 -I$(SLINT)/include/slint
LDFLAGS := -L$(SLINT)/lib -Wl,-rpath,'$$ORIGIN/$(SLINT)/lib' -lslint_cpp

TARGET := app

all: $(TARGET)

ui.h: ui.slint
\t$(SLINT_COMPILER) ui.slint -o ui.h

$(TARGET): main.cpp ui.h
\t$(CXX) $(CXXFLAGS) main.cpp -o $(TARGET) $(LDFLAGS)

run: $(TARGET)
\t./$(TARGET)

clean:
\trm -f $(TARGET) ui.h
'''
    )


def install_slint(stdscr):
    project = Path.cwd()
    destination = project / "vendor" / "slint"

    status(stdscr, "Suche aktuellen Slint-Release ...")

    asset_name, asset_url = find_slint_asset()

    status(stdscr, f"Lade {asset_name} ...")

    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)

        archive = temp / "slint.tar.gz"
        extracted = temp / "extracted"

        download(asset_url, archive)

        status(stdscr, "Entpacke Slint ...")

        extracted.mkdir()

        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(extracted)

        bin_dir = find_directory(extracted, "bin")
        include_dir = find_directory(extracted, "include")
        lib_dir = find_directory(extracted, "lib")

        if not bin_dir or not include_dir or not lib_dir:
            raise RuntimeError(
                "Slint SDK Struktur wurde nicht erkannt."
            )

        status(stdscr, "Kopiere Slint ins Projekt ...")

        copy_directory(
            bin_dir,
            destination / "bin"
        )

        copy_directory(
            include_dir,
            destination / "include"
        )

        copy_directory(
            lib_dir,
            destination / "lib"
        )

    create_main_cpp(project)
    create_ui(project)
    create_makefile(project)

    status(
        stdscr,
        "Slint installiert!  make  oder  make run"
    )

    stdscr.addstr(5, 2, "Taste drücken zum Beenden.")
    stdscr.refresh()
    stdscr.getch()


def main(stdscr):
    curses.curs_set(0)

    try:
        install_slint(stdscr)

    except Exception as error:
        status(stdscr, f"FEHLER: {error}")
        stdscr.addstr(5, 2, "Taste drücken.")
        stdscr.getch()


if __name__ == "__main__":
    curses.wrapper(main)
