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
    fixture = "../aports/main/linux-postmarketos/APKBUILD"

    env = {
        "CARCH": "armhf",
        "srcdir": "/home/src",
        "CBUILD_ARCH": "arm",
        "_kernver": "1.2.3",
        "CROSS_COMPILE": "test"
    }

    shell = ShellParser(open(fixture), environment=env)
    assert shell.variables["_flavor"] == "postmarketos"


@pytest.fixture
def args(request):
    import pmb.parse
    sys.argv = ["pmbootstrap.py", "chroot"]
    args = pmb.parse.arguments()
    return args


def test_apkbuild_parser(args):
    fixture = "../aports/main/linux-postmarketos/APKBUILD"

    result = apkbuild(args, fixture)
    assert result["pkgname"] == "linux-postmarketos"

    assert isinstance(result["arch"], list)
    assert len(result["arch"]) == 1
    assert result["arch"][0] == "all"

    assert isinstance(result["depends"], list)
    assert len(result["depends"]) == 1
    assert result["depends"][0] == "postmarketos-mkinitfs"

    assert isinstance(result["makedepends"], list)
    assert len(result["makedepends"]) == 8
    assert set(result["makedepends"]) == {"perl", "sed", "installkernel", "bash", "gmp-dev", "bc", "linux-headers",
                                          "elfutils-dev"}

    assert isinstance(result["options"], list)
    assert len(result["options"]) == 3
    assert set(result["options"]) == {"!strip", "!check", "!tracedeps"}

    assert result["pkgrel"] == "4"
    assert result["pkgver"] == "4.12.4"

    assert isinstance(result["subpackages"], list)
    assert len(result["subpackages"]) == 1
    assert set(result["subpackages"]) == {"linux-postmarketos-dev"}
