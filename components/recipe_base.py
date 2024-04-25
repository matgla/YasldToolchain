# -*- coding: utf-8 -*-

#
# recipe_base.py
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

import wget
import sys
from urllib.parse import urlparse
from pathlib import Path
from hashlib import sha256
from tqdm import tqdm
import tarfile
import zipfile

is_build_recipe = False


class RecipeBase:
    def __init__(self, **kwargs):
        if "name" in kwargs:
            self.name = kwargs["name"]
        else:
            raise RuntimeError("'name' must be provided")
        if "source" in kwargs:
            self.source = kwargs["source"]
        else:
            raise RuntimeError("'source' must be provided")
        if "sha" in kwargs:
            self.sha = kwargs["sha"]
        if "output" in kwargs:
            self.output = kwargs["output"]
            self.sources_directory = Path(self.output) / "sources"
            self.download_directory = self.sources_directory / "download"
        else:
            raise RuntimeError("'output' path must be provided")

    def _calculate_hash(self, filepath):
        hash = sha256()
        with open(filepath, "rb") as file:
            chunk = 0
            while chunk != b"":
                chunk = file.read(1024)
                hash.update(chunk)
        return hash.hexdigest()

    def fetch(self):
        filename = os.path.basename(urlparse(self.source).path).strip()
        self.source_file = self.download_directory / filename
        print(" - fetching file:", self.source)
        if os.path.exists(self.source_file):
            if self.sha is None:
                print("     file already fetched")
                return
            else:
                calculated_sha = self._calculate_hash(self.source_file)
                if calculated_sha == self.sha:
                    print("     file already fetched")
                    return
                else:
                    print("     SHA256 doesn't match, file be fetched again")
                    print("       Expected  :", self.sha)
                    print("       Calculated:", calculated_sha)
            os.remove(self.source_file)

        wget.download(str(self.source), str(self.source_file))
        print("")

    def _unpack_with_progress_bar(self, file, target):
        if str(file).lower().endswith(".zip"):
            with zipfile.ZipFile(file) as zip:
                for member in tqdm(
                    zip.infolist()
                ):
                    if not os.path.exists(Path(target) / member.filename):
                        zip.extract(member=member, path=target)

        else:
            with tarfile.open(name=file) as tar:
                for member in tqdm(
                    iterable=tar.getmembers(), total=len(tar.getmembers())
                ):
                    if not os.path.exists(Path(target) / member.path):
                        tar.extract(member=member, path=target)


    def unpack(self):
        print(" - Extracting archive:", self.source_file)
        calculated_sha = self._calculate_hash(self.source_file)
        if calculated_sha != self.sha:
            print("     SHA256 doesn't match, aborting...")
            print("       Expected  :", self.sha)
            print("       Calculated:", calculated_sha)

            sys.exit(-1)

        self._unpack_with_progress_bar(
            self.source_file, self.sources_directory / self.name
        )

    def configure(self):
        raise RuntimeError("Called configure from base class")

    def compile(self):
        raise RuntimeError("Called build from base class")

    def install(self):
        raise RuntimeError("Called install from base class")

    def build(self):
        self.fetch()
        self.unpack()
        self.configure()
        self.compile()
        self.install()
