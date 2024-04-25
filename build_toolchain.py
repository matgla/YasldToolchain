#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# build_toolchain.py
#
# Copyright (C) 2023 Mateusz Stadnik <matgla@live.com>
#
# This program is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General
# Public License along with this program. If not, see
# <https://www.gnu.org/licenses/>.
#

import os
import sys
from pathlib import Path
import argparse
import importlib
import importlib.util
import subprocess
import glob


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog=os.path.basename(__file__),
        description="Build Yasld Toolchain",
        epilog="""
            Usages will be here
            """,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-b",
        "--build-dir",
        default="build",
        help="Build directory for Yasld Toolchain",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="build/output",
        help="Install directory for Yasld Toolchain",
    )
    parser.add_argument(
        "-c",
        "--components",
        default="all",
        help="Filter components to build, list with ',' \
            delimiter, 'all' to build all",
    )
    parser.add_argument(
        "-s",
        "--show-components",
        action="store_true",
        help="Show components available to build",
    )
    parser.add_argument(
        "-n",
        "--no-verify",
        default=False,
        action="store_true",
        help="Scripts components verification, i.e. for building from master"
    )

    args, _ = parser.parse_known_args()
    return args


def load_recipe(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


components_directory = Path(__file__).parent / "components"


def get_available_components():
    components = []
    for file in os.listdir(components_directory):
        if os.path.isfile(components_directory / file):
            possible_recipe = load_recipe(
                Path(file).stem, components_directory / file
            )
            if (
                hasattr(possible_recipe, "is_build_recipe")
                and possible_recipe.is_build_recipe
            ):
                components.append(Path(file).stem)
    return components


def show_available_components(components):
    print("Available components:")
    for component in components:
        print(" - " + component)


def filter_components(components, allowed_components):
    return [value for value in components if value in allowed_components]


def print_options(components, args):
    print(" - build directory:  ", args.build_dir)
    print(" - output directory: ", args.output_dir)
    print(" - components:       ", components)


def build_component(component, output_directory, prefix, skip_verification):
    if os.path.exists(Path(output_directory) / (component + "_done")):
        return

    recipe = load_recipe(component, components_directory / (component + ".py"))

    if not hasattr(recipe, "get_recipe"):
        print(
            " - ERROR, component ignored:",
            component,
            ". Lack of 'get_recipe'",
        )
    else:
        if hasattr(recipe, "dependencies"):
            for dependency in recipe.dependencies:
                build_component(dependency, output_directory, prefix, skip_verification)

        recipe.get_recipe(output_directory, prefix, skip_verification).build()
        # If finished everything was built correctly
        (Path(output_directory) / (component + "_done")).touch()


def process_components(components, output_directory, skip_verification):
    prefix = (Path(output_directory) / "yasld-toolchain").resolve()
    for component in components:
        build_component(component, output_directory, prefix, skip_verification)


def strip_toolchain(output_directory):
    result = subprocess.run(
        "find "
        + str(output_directory)
        + "/bin -type f -and \( -executable \) -exec strip '{}' \;",
        shell=True,
    )

    assert result.returncode == 0

    print("Removing {prefix}/lib/libcc1.*".format(prefix=output_directory))
    files = glob.glob("{prefix}/lib/libcc1*".format(prefix=output_directory))

    for file in files:
        os.remove(file)


def main():
    args = parse_arguments()
    components = get_available_components()
    if args.show_components:
        show_available_components(components)
        sys.exit(0)

    if args.components != "all":
        components = filter_components(components, args.components)

    print_options(components, args)
    (Path(args.build_dir) / "sources" / "download").mkdir(
        parents=True, exist_ok=True
    )
    process_components(components, args.build_dir, args.no_verify)
    strip_toolchain(Path(args.build_dir) / "yasld-toolchain")


if __name__ == "__main__":
    main()
