import json
from pathlib import Path


def load_project_config(project):
    file = project / "cpm.json"

    if not file.exists():
        return {
            "name": "app",
            "packages": []
        }

    return json.loads(
        file.read_text()
    )


def save_project_config(project, config):
    file = project / "cpm.json"

    file.write_text(
        json.dumps(
            config,
            indent=4
        )
        + "\n"
    )


def add_package_to_project(project, package_name):
    config = load_project_config(project)

    packages = config.setdefault(
        "packages",
        []
    )

    if package_name not in packages:
        packages.append(package_name)

    save_project_config(
        project,
        config
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


def create_slint_ui(project):
    file = project / "ui.slint"

    if file.exists():
        return

    file.write_text(
'''export component App inherits Window {
    width: 400px;
    height: 240px;
    title: "CPM Slint";

    background: #202020;

    Text {
        text: "Hallo aus C++!";
        color: white;
        font-size: 28px;

        horizontal-alignment: center;
        vertical-alignment: center;
    }
}
'''
    )


def collect_flags(packages):
    cxxflags = []
    ldflags = []

    for package in packages:
        if package["cxxflags"]:
            cxxflags.append(
                package["cxxflags"]
            )

        if package["ldflags"]:
            ldflags.append(
                package["ldflags"]
            )

    return cxxflags, ldflags


def generate_makefile(project, packages):
    cxxflags, ldflags = collect_flags(packages)

    has_slint = any(
        package["package_type"] == "slint"
        for package in packages
    )

    cxxflags_text = " ".join(cxxflags)
    ldflags_text = " ".join(ldflags)

    if has_slint:
        makefile = f'''CXX := g++
TARGET := app

SLINT_COMPILER := vendor/slint/bin/slint-compiler

CXXFLAGS := -std=c++20 {cxxflags_text}
LDFLAGS := {ldflags_text}

all: $(TARGET)

ui.h: ui.slint
\t$(SLINT_COMPILER) ui.slint -o ui.h

$(TARGET): main.cpp ui.h
\t$(CXX) $(CXXFLAGS) main.cpp -o $(TARGET) $(LDFLAGS)

run: $(TARGET)
\t./$(TARGET)

clean:
\trm -f $(TARGET) ui.h

.PHONY: all run clean
'''

    else:
        makefile = f'''CXX := g++
TARGET := app

CXXFLAGS := -std=c++20 {cxxflags_text}
LDFLAGS := {ldflags_text}

all: $(TARGET)

$(TARGET): main.cpp
\t$(CXX) $(CXXFLAGS) main.cpp -o $(TARGET) $(LDFLAGS)

run: $(TARGET)
\t./$(TARGET)

clean:
\trm -f $(TARGET)

.PHONY: all run clean
'''

    (project / "Makefile").write_text(
        makefile
    )
