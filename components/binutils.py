# -*- coding: utf-8 -*-

#
# binutils.py
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


from recipe_base import RecipeBase

import subprocess

is_build_recipe = True


class BinutilsRecipe(RecipeBase):
    version = "2.41"
    sha256 = "ae9a5789e23459e59606e6714723f2d3ffc31c03174191ef0d015bdf06007450"
    target = "arm-none-eabi"

    def __init__(self, output_directory, prefix):
        super().__init__(
            name="binutils",
            source="https://ftp.gnu.org/gnu/binutils/binutils-{version}.tar.xz".format(
                version=BinutilsRecipe.version
            ),
            output=output_directory,
            sha=BinutilsRecipe.sha256,
        )

        self.prefix = prefix

    def configure(self):
        self.sources_root = (
            self.sources_directory
            / self.name
            / "binutils-{version}".format(version=BinutilsRecipe.version)
        )
        print(" - Configure:", self.sources_root)
        self.build_directory = self.sources_root / "build"
        self.build_directory.mkdir(parents=True, exist_ok=True)

        subprocess.run(
            'sed -i "/ac_cpp=/s/\\$CPPFLAGS/\\$CPPFLAGS -O2/',
            shell=True,
            cwd=self.sources_root,
        )

        args = ["../configure"]
        args.extend(
            [
                "--target={target}".format(target=BinutilsRecipe.target),
                "--prefix={prefix}".format(prefix=self.prefix),
                "--with-sysroot={prefix}/{target}".format(
                    prefix=self.prefix, target=BinutilsRecipe.target
                ),
                "--enable-multilib",
                "--enable-interwork",
                "--with-gnu-as",
                "--with-gnu-ld",
                "--disable-nls",
                "--enable-ld=default",
                "--enable-gold",
                "--enable-plugins",
                "--enable-deterministic-archives",
            ]
        )

        print(" - Configure called with:", subprocess.list2cmdline(args))
        subprocess.run(
            subprocess.list2cmdline(args), shell=True, cwd=self.build_directory
        )

    def compile(self):
        subprocess.run(
            "make -j$(nproc)",
            shell=True,
            cwd=self.build_directory,
        )

    def install(self):
        subprocess.run("make install", shell=True, cwd=self.build_directory)


def get_recipe(output_directory, prefix):
    return BinutilsRecipe(output_directory, prefix)
