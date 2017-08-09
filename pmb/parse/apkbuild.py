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
import logging
import pmb.config
from pmb.parse.shell import ShellParser


def cut_off_function_names(apkbuild):
    """
    For subpackages: only keep the subpackage name, without the internal
    function name, that tells how to build the subpackage.
    """
    sub = apkbuild["subpackages"]
    for i in range(len(sub)):
        sub[i] = sub[i].split(":", 1)[0]
    apkbuild["subpackages"] = sub
    return apkbuild


def apkbuild(args, path):
    """
    Parse relevant information out of the APKBUILD file.
    This should process all the relevant edge-cases for APKBUILD parsing.

    :param path: Full path to the APKBUILD
    :returns: Relevant variables from the APKBUILD. Arrays get returned as
        arrays.
    """
    # Try to get a cached result first (we assume, that the aports don't change
    # in one pmbootstrap call)
    if path in args.cache["apkbuild"]:
        return args.cache["apkbuild"][path]

    # Specify environment variables used by APKBUILD scripts
    env = {
        "CARCH": "",
        "srcdir": "",
        "CBUILD_ARCH": "",
        "_kernver": "",
        "CROSS_COMPILE": ""
    }

    with open(path, encoding="utf-8") as handle:
        parsed = ShellParser(handle, environment=env)

    # Parse all attributes from the config
    ret = {}
    for attribute, options in pmb.config.apkbuild_attributes.items():
        if attribute in parsed.variables:
            value = parsed.variables[attribute]
            if options["array"]:
                if value == "":
                    value = []
                else:
                    value = value.split(" ")
            ret[attribute] = value

    # Add missing keys
    for attribute, options in pmb.config.apkbuild_attributes.items():
        if attribute not in ret:
            if options["array"]:
                ret[attribute] = []
            else:
                ret[attribute] = ""

    # Properly format values
    ret = cut_off_function_names(ret)

    # Sanity check: pkgname
    suffix = "/" + ret["pkgname"] + "/APKBUILD"
    if not os.path.realpath(path).endswith(suffix):
        logging.info("Folder: '" + os.path.dirname(path) + "'")
        logging.info("Pkgname: '" + ret["pkgname"] + "'")
        raise RuntimeError("The pkgname must be equal to the name of"
                           " the folder, that contains the APKBUILD!")

    # Fill cache
    args.cache["apkbuild"][path] = ret
    return ret
