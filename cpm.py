#!/usr/bin/env python3

import curses
import sys

from pathlib import Path

from database import (
    get_package,
    list_packages
)

from installer import install_package

from generator import (
    add_package_to_project,
    create_main_cpp,
    create_slint_ui,
    create_sdl2_main,
    generate_makefile,
    load_project_config
)


def status(stdscr, text):
    stdscr.clear()

    stdscr.addstr(
        1,
        2,
        "CPM - C++ Package Manager"
    )

    stdscr.addstr(
        3,
        2,
        text
    )

    stdscr.refresh()


def load_project_packages(project):
    config = load_project_config(project)

    packages = []

    for name in config.get("packages", []):
        package = get_package(name)

        if package:
            packages.append(package)

    return packages


def command_install(stdscr, package_name):
    project = Path.cwd()

    package = get_package(
        package_name
    )

    if not package:
        status(
            stdscr,
            f"Unbekanntes Paket: {package_name}"
        )

        stdscr.addstr(
            5,
            2,
            "Taste drücken."
        )

        stdscr.getch()

        return

    install_package(
        package,
        project,
        lambda text: status(
            stdscr,
            text
        )
    )

    add_package_to_project(
        project,
        package_name
    )

    if package["package_type"] == "slint":
        create_main_cpp(project)
        create_slint_ui(project)

    elif package["package_type"] == "sdl2":
        create_sdl2_main(project)

    packages = load_project_packages(
        project
    )

    generate_makefile(
        project,
        packages
    )

    status(
        stdscr,
        f"{package_name} installiert."
    )

    stdscr.addstr(
        5,
        2,
        "Jetzt: make oder make run"
    )

    stdscr.addstr(
        7,
        2,
        "Taste drücken."
    )

    stdscr.refresh()
    stdscr.getch()


def command_list(stdscr):
    packages = list_packages()

    stdscr.clear()

    stdscr.addstr(
        1,
        2,
        "CPM - verfügbare Pakete"
    )

    row = 3

    for package in packages:
        stdscr.addstr(
            row,
            4,
            package["name"]
        )

        row += 1

    stdscr.addstr(
        row + 2,
        2,
        "Taste drücken."
    )

    stdscr.refresh()
    stdscr.getch()


def show_usage():
    print(
        """
CPM - C++ Package Manager

Benutzung:

    cpm install <paket>
    cpm list

Beispiele:

    cpm install slint
    cpm list
"""
    )


def curses_main(stdscr):
    curses.curs_set(0)

    if len(sys.argv) < 2:
        status(
            stdscr,
            "Kein Befehl angegeben."
        )

        stdscr.addstr(
            5,
            2,
            "Benutze: cpm install slint"
        )

        stdscr.addstr(
            7,
            2,
            "Taste drücken."
        )

        stdscr.getch()

        return

    command = sys.argv[1]

    try:
        if command == "install":
            if len(sys.argv) < 3:
                raise RuntimeError(
                    "Paketname fehlt."
                )

            package_name = sys.argv[2]

            command_install(
                stdscr,
                package_name
            )

        elif command == "list":
            command_list(
                stdscr
            )

        elif command == "clean":
            command_clean(stdscr)


        else:
            raise RuntimeError(
                f"Unbekannter Befehl: {command}"
            )

    except Exception as error:
        status(
            stdscr,
            f"FEHLER: {error}"
        )

        stdscr.addstr(
            5,
            2,
            "Taste drücken."
        )

        stdscr.getch()


def command_clean(stdscr):
    project = Path.cwd()

    files = [
        "Makefile",
        "cpm.json",
        "main.cpp",
        "ui.slint",
        "ui.h",
        "app",
        "app.exe",
    ]

    for name in files:
        path = project / name

        if path.exists():
            path.unlink()

    vendor = project / "vendor"

    if vendor.exists():
        import shutil
        shutil.rmtree(vendor)

    status(
        stdscr,
        "Projekt wurde bereinigt."
    )

    stdscr.addstr(
        5,
        2,
        "Taste drücken."
    )

    stdscr.getch()

def main():
    if len(sys.argv) == 2 and sys.argv[1] in (
        "--help",
        "-h"
    ):
        show_usage()
        return

    curses.wrapper(
        curses_main
    )


if __name__ == "__main__":
    main()
