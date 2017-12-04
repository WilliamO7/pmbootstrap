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
import fnmatch
import pmb.config
import pmb.chroot.apk
import pmb.parse.arch


def arch(args, pkgname):
    """
    Find a good default in case the user did not specify for which architecture
    a package should be built.

    :returns: native architecture (x86_64 in most cases) when the APKBUILD has
              "noarch" or "all". Otherwise the first architecture in the
              APKBUILD.
    """
    aport = pmb.build.find_aport(args, pkgname)
    apkbuild = pmb.parse.apkbuild(args, aport + "/APKBUILD")
    if "noarch" in apkbuild["arch"] or "all" in apkbuild["arch"]:
        return args.arch_native
    return apkbuild["arch"][0]


def suffix(args, apkbuild, arch):
    if arch == args.arch_native:
        return "native"

    pkgname = apkbuild["pkgname"]
    if pkgname.endswith("-repack"):
        return "native"
    if args.cross:
        for pattern in pmb.config.build_cross_native:
            if fnmatch.fnmatch(pkgname, pattern):
                return "native"

    return "buildroot_" + arch


def crosscompile(args, apkbuild, arch, suffix):
    """
        :returns: None, "native" or "distcc"
    """
    if not args.cross:
        return None
    if apkbuild["pkgname"].endswith("-repack"):
        return None
    if not pmb.parse.arch.cpu_emulation_required(args, arch):
        return None
    if suffix == "native":
        return "native"
    return "distcc"
