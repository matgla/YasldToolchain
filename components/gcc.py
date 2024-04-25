# -*- coding: utf-8 -*-

#
# gcc.py
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
import shutil
from pathlib import Path

is_build_recipe = True


class GccRecipe(RecipeBase):
    gcc_version = "master"
    sha256 = "f2214c3bae925fbf5559b708c354130e98cda4e7fbcfb63043ce43757b675833"
    target = "arm-none-eabi"

    def __init__(self, output_directory, prefix):
        super().__init__(
            name="gcc",
            source="https://github.com/gcc-mirror/gcc/archive/refs/heads/master.zip",
            output=output_directory,
            sha=GccRecipe.sha256,
        )
        self.prefix = prefix

        self.env = os.environ.copy()
        self.env[
            "CFLAGS_FOR_TARGET"
        ] = "-g -Os -ffunction-sections -fdata-sections \
"

        self.env["CXXFLAGS_FOR_TARGET"] = self.env["CFLAGS_FOR_TARGET"]

        self.env_nano = os.environ.copy()
        self.env_nano["CFLAGS_FOR_TARGET"] = self.env["CFLAGS_FOR_TARGET"]
        self.env_nano["CXXFLAGS_FOR_TARGET"] = (
            self.env_nano["CFLAGS_FOR_TARGET"] + " -fno-exceptions"
        )

        self.sources_root = (
            self.sources_directory
            / self.name
            / "gcc-{version}".format(version=GccRecipe.gcc_version)
        )

        self.nano_build_directory = self.sources_root / "build_nano"
        self.nano_build_directory.mkdir(parents=True, exist_ok=True)
        self.build_directory = self.sources_root / "build"
        self.build_directory.mkdir(parents=True, exist_ok=True)

    def configure(self):
        print(" - Configure:", self.sources_root)

        args = ["../configure"]
        args.extend(
            [
                "--target={target}".format(target=GccRecipe.target),
                "--prefix={prefix}".format(prefix=self.prefix),
                "--with-sysroot={prefix}/{target}".format(
                    prefix=self.prefix, target=GccRecipe.target
                ),
                "--with-native-system-header-dir=/include",
                "--libexecdir={prefix}/{target}/lib".format(
                    prefix=self.prefix, target=GccRecipe.target
                ),
                "--enable-languages=c,c++",
                "--enable-plugins",
                "--disable-decimal-float",
                "--disable-libffi",
                "--disable-libstdcxx-pch",
                "--disable-libgomp",
                "--disable-libmudflap",
                "--disable-libquadmath",
                "--disable-libssp",
                "--disable-nls",
                "--enable-shared=libgcc",
                "--disable-threads",
                "--disable-tls",
                "--with-gnu-ld",
                "--with-gnu-as",
                "--with-system-zlib",
                "--with-newlib",
                "--with-headers={prefix}/{target}/include".format(
                    prefix=self.prefix, target=GccRecipe.target
                ),
                "--with-python-dir=share/gcc-arm-none-eabi",
                # "--with-gmp",
                # "--with-mpfr",
                "--with-isl",
                # "--with-mpc",
                "--with-libelf",
                "--enable-gnu-indirect-function",
                "--with-host-libstdc++='-static-libgcc -Wl,-Bstatic,-lstdc++,-Bdynamic -lm'"
                "--with-pkgversion='Yasld Toolchain'",
                "--with-multilib-list=rmprofile",
            ]
        )
        print(" - Fixing permissions ")
        result = subprocess.run(
            "chmod +x ../configure ../install-sh ../move-if-change ../libgcc/mkheader.sh ../contrib/download_prerequisites",
            shell=True,
            cwd=self.build_directory,
            env=self.env,
        )

        print(self.sources_directory)
        result = subprocess.run(
            "contrib/download_prerequisites",
            shell=True,
            cwd=self.sources_root,
            env=self.env,
        )
        
        assert result.returncode == 0

        print(" - Configure called with:", subprocess.list2cmdline(args))
        if not os.path.exists(self.build_directory / ".configure_done"):
            result = subprocess.run(
                subprocess.list2cmdline(args),
                shell=True,
                cwd=self.build_directory,
                env=self.env,
            )

            assert result.returncode == 0
            (self.build_directory / ".configure_done").touch()

        print(
            " - Configure for nano called with:", subprocess.list2cmdline(args)
        )

        if not os.path.exists(self.nano_build_directory / ".configure_done"):
            result = subprocess.run(
                subprocess.list2cmdline(args),
                shell=True,
                cwd=self.nano_build_directory,
                env=self.env_nano,
            )

            assert result.returncode == 0
            (self.nano_build_directory / ".configure_done").touch()

    def compile(self):
        result = subprocess.run(
            'make -j4 INHIBIT_LIBC_CFLAGS="-DUSE_TM_CLONE_REGISTRY=0"',
            shell=True,
            cwd=self.build_directory,
            env=self.env,
        )

        assert result.returncode == 0

        result = subprocess.run(
            'make -j4 INHIBIT_LIBC_CFLAGS="-DUSE_TM_CLONE_REGISTRY=0"',
            shell=True,
            cwd=self.nano_build_directory,
            env=self.env_nano,
        )

        assert result.returncode == 0

    def install(self):
        print("Installing GCC nano libraries")

        subprocess.run("make install", shell=True, cwd=self.build_directory)
        
        result = subprocess.run(
            "./gcc/gcc-cross -print-multi-lib",
            shell=True,
            cwd=self.nano_build_directory,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        for lib in result.stdout.split("\n"):
            print(lib)
            arch = lib.split(";")[0].strip()
            if len(arch) == 0:
                continue
            print("Processing architecture:", arch)
            archpath = Path(self.nano_build_directory / self.target / arch)

            target = self.prefix / self.target / "lib" / arch

            for path in archpath.rglob("libstdc++.a"):
                source_libstdcpp = path
                print(
                    "Copying {} to {}".format(
                        source_libstdcpp, target / "libstdc++_nano.a"
                    )
                )
                shutil.copyfile(source_libstdcpp, target / "libstdc++_nano.a")
                break

            for path in archpath.rglob("libsupc++.a"):
                source_libsupcpp = path
                print(
                    "Copying {} to {}".format(
                        source_libsupcpp, target / "libsupc++_nano.a"
                    )
                )
                shutil.copyfile(source_libsupcpp, target / "libsupc++_nano.a")
                break



def get_recipe(output_directory, prefix):
    return GccRecipe(output_directory, prefix)


dependencies = ["newlib"]
