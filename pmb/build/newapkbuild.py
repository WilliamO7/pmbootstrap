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
import glob
import os
import logging
import pmb.chroot.user
import pmb.helpers.cli
import pmb.parse.apkbuild


def newapkbuild(args, folder, args_passed):
    # Initialize build environment and temp folder
    pmb.build.init(args)
    temp = "/tmp/newapkbuild"
    temp_outside = args.work + "/chroot_native" + temp
    if os.path.exists(temp_outside):
        pmb.chroot.root(args, ["rm", "-r", temp])
    pmb.chroot.user(args, ["mkdir", "-p", temp])

    # Run newapkbuild
    pmb.chroot.user(args, ["newapkbuild"] + args_passed, log=False,
                    working_dir=temp)
    glob_result = glob.glob(temp_outside + "/*/APKBUILD")
    if not len(glob_result):
        return

    # Paths for copying
    source_apkbuild = glob_result[0]
    pkgname = pmb.parse.apkbuild(args, source_apkbuild)["pkgname"]
    source = os.path.dirname(source_apkbuild)
    target = args.aports + "/" + folder + "/" + pkgname

    # Overwrite confirmation
    if os.path.exists(target):
        logging.warning("WARNING: Folder already exists: " + target)
        if not pmb.helpers.cli.confirm(args, "Continue and delete its"
                                       " contents?"):
            raise RuntimeError("Aborted.")
        pmb.helpers.run.user(args, ["rm", "-r", target])

    # Copy the APKBUILD
    logging.info("Create " + target)
    pmb.helpers.run.user(args, ["mkdir", "-p", args.aports + "/" + folder])
    pmb.helpers.run.user(args, ["cp", "-r", source, target])
