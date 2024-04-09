# -*- coding: utf-8 -*-
#
# newlib.py
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


from components.recipe_base import RecipeBase

import subprocess
import os

is_build_recipe = True


class NewlibRecipe(RecipeBase):
    version = "4.4.0.20231231"
    sha256 = "0c166a39e1bf0951dfafcd68949fe0e4b6d3658081d6282f39aeefc6310f2f13"
    target = "arm-none-eabi"

    def __init__(self, output_directory, prefix):
        super().__init__(
            name="newlib",
            source="https://sourceware.org/pub/newlib/newlib-{version}.tar.gz".format(
                version=NewlibRecipe.version
            ),
            output=output_directory,
            sha=NewlibRecipe.sha256,
        )
        self.prefix = prefix
        self.env = os.environ.copy()
        self.env[
            "CFLAGS_FOR_TARGET"
        ] = "-g -Os -ffunction-sections -fdata-sections \
"

    def configure(self):
        self.sources_root = (
            self.sources_directory
            / self.name
            / "newlib-{version}".format(version=NewlibRecipe.version)
        )
        print(" - Configure:", self.sources_root)
        self.nano_build_directory = self.sources_root / "build-nano"
        self.nano_build_directory.mkdir(parents=True, exist_ok=True)

        args = ["../configure"]
        args.extend(
            [
                "--target={target}".format(target=NewlibRecipe.target),
                "--prefix={prefix}".format(prefix=self.prefix),
                "--disable-newlib-supplied-syscalls",
                "--enable-newlib-reent-small",
                "--enable-newlib-retargetable-locking",
                "--disable-newlib-fvwrite-in-streamio",
                "--disable-newlib-fseek-optimization",
                "--disable-newlib-wide-orient",
                "--enable-newlib-nano-malloc",
                "--disable-newlib-unbuf-stream-opt",
                "--enable-lite-exit",
                "--enable-newlib-global-atexit",
                "--enable-newlib-nano-formatted-io",
                "--disable-nls",
            ]
        )

        print(" - Configure called with:", subprocess.list2cmdline(args))
        subprocess.run(
            subprocess.list2cmdline(args),
            shell=True,
            cwd=self.nano_build_directory,
            env=self.env,
        )

        self.full_build_directory = self.sources_root / "build-full"
        self.full_build_directory.mkdir(parents=True, exist_ok=True)

        args = ["../configure"]
        args.extend(
            [
                "--target={target}".format(target=NewlibRecipe.target),
                "--prefix={prefix}".format(prefix=self.prefix),
                "--enable-newlib-io-long-long",
                "--enable-newlib-io-c99-formats",
                "--enable-newlib-register-fini",
                "--enable-newlib-retargetable-locking",
                "--disable-newlib-supplied-syscalls",
                "--disable-nls",
            ]
        )

        print(" - Configure called with:", subprocess.list2cmdline(args))
        subprocess.run(
            subprocess.list2cmdline(args),
            shell=True,
            cwd=self.full_build_directory,
            env=self.env,
        )

    def compile(self):
        subprocess.run(
            "make -j$(nproc)",
            shell=True,
            cwd=self.nano_build_directory,
            env=self.env,
        )

        subprocess.run(
            "make -j$(nproc)",
            shell=True,
            cwd=self.full_build_directory,
            env=self.env,
        )

    def install(self):
        subprocess.run(
            "make install", shell=True, cwd=self.nano_build_directory
        )
        subprocess.run(
            'find "{prefix}" -regex ".*/lib\(c\|g\|rdimon\)\.a" -exec rename .a _nano.a \'{braces}\' \;'.format(
                prefix=self.prefix, braces="{}"
            ),
            shell=True,
            cwd=self.nano_build_directory,
        )
        subprocess.run(
            "make install", shell=True, cwd=self.full_build_directory
        )


def get_recipe(output_directory, prefix):
    return NewlibRecipe(output_directory, prefix)
