"""
Copyright 2017 Oliver Smith

This file is part of pmbootstrap.

pmbootstrap is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

pmbootstrap is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pmbootstrap.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys
import pytest

sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__) + "/..")))

from pmb.parse.shell import ShellParser
from pmb.parse.apkbuild import apkbuild


@pytest.mark.parametrize("shell_script,expected", [
    ("TEST=ABC", {"TEST": "ABC"}),
    ("TEST=\"ABC\"", {"TEST": "ABC"}),
    ("TEST=\"ABC\"\nFOO=BAR", {"TEST": "ABC", "FOO": "BAR"}),
    ("a=1\nB=2\n_c=3\n_D=4", {"a": "1", "B": "2", "_c": "3", "_D": "4"}),
    ("foo=bar\nbaz=$foo", {"foo": "bar", "baz": "bar"}),
    ("foo=bar\nbaz=${foo}", {"foo": "bar", "baz": "bar"}),
    ("foo=bar\nbaz=test${foo}test", {"foo": "bar", "baz": "testbartest"}),
    ("foo=bar\nvar=foo\nbaz=${${var}}", {"foo": "bar", "var": "foo", "baz": "bar"}),
    ("HOSTCC=arm-linux-gnueabi-clang\nCROSS_COMPILE=arm-linux-gnueabi-\nCC=\"${HOSTCC#${CROSS_COMPILE}}\"",
     {"HOSTCC": "arm-linux-gnueabi-clang", "CROSS_COMPILE": "arm-linux-gnueabi-", "CC": "clang"}),
    ("foo=bar\nfoo=baz", {"foo": "baz"})
])
def test_simple(shell_script, expected):
    parsed = ShellParser(shell_script)
    for key, value in expected.items():
        assert parsed.variables[key] == value


def test_apkbuild():
    fixture = "../aports/main/hello-world/APKBUILD"

    env = {
        "CARCH": "armhf",
        "srcdir": "/home/src",
        "CBUILD_ARCH": "arm",
        "_kernver": "1.2.3",
        "CROSS_COMPILE": "test"
    }

    shell = ShellParser(open(fixture), environment=env)
    assert shell.variables["pkgname"] == "hello-world"


@pytest.fixture
def args(request):
    import pmb.parse
    sys.argv = ["pmbootstrap.py", "chroot"]
    args = pmb.parse.arguments()
    return args


def test_apkbuild_parser(args):
    fixture = "../aports/main/hello-world-wrapper/APKBUILD"

    result = apkbuild(args, fixture)
    assert result["pkgname"] == "hello-world-wrapper"

    assert isinstance(result["arch"], list)
    assert len(result["arch"]) == 1
    assert result["arch"][0] == "noarch"

    assert isinstance(result["depends"], list)
    assert len(result["depends"]) == 1
    assert result["depends"][0] == "hello-world"

    assert isinstance(result["makedepends"], list)
    assert len(result["makedepends"]) == 1
    assert result["makedepends"][0] == "hello-world"

    assert isinstance(result["options"], list)
    assert len(result["options"]) == 0

    assert result["pkgrel"] == "1"
    assert result["pkgver"] == "1"

    assert isinstance(result["subpackages"], list)
    assert len(result["subpackages"]) == 0
