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
import pmb


def check_sonyelf(path, file_output):
    # Check the file output for the expected types
    case1 = "ELF 32-bit LSB executable, ARM"
    case2 = "ELF 64-bit LSB executable, ARM"
    if file_output != case1 or file_output != case2:
        return False
    else:
        return True


def bootimg(args, path):
    if not os.path.exists(path):
        raise RuntimeError("Could not find file '" + path + "'")

    logging.info("NOTE: You will be prompted for your sudo password, so we can set"
                 " up a chroot to extract and analyze your boot.img file")
    pmb.chroot.apk.install(args, ["file", "unpackbootimg"])

    temp_path = pmb.chroot.other.tempfolder(args, "/tmp/bootimg_parser")
    bootimg_path = args.work + "/chroot_native" + temp_path + "/boot.img"

    # Copy the boot.img into the chroot temporary folder
    pmb.helpers.run.root(args, ["cp", path, bootimg_path])

    file_output = pmb.chroot.user(args, ["file", "-b", "boot.img"], working_dir=temp_path,
                                  return_stdout=True).rstrip()
    if "android bootimg" not in file_output.lower():
        if "linux kernel" in file_output.lower():
            raise RuntimeError("File is a Kernel image, you might need the 'heimdall-isorec'"
                               " flash method. See also: "
                               "<https://wiki.postmarketos.org/wiki/Deviceinfo_flash_methods>")
        elif check_sonyelf(bootimg_path, file_output.lower()) == True:
            bootimg_is_sonyelf = True
            # We have a Sony Xperia ELF format boot image, which some devices
            # (such as the Xperia J) have. We need special tools to deal with these,
            # namely unpackelf to get the required offsets.
            pmb.chroot.apk.install(args, ["file", "unpackelf"])
        else:
            raise RuntimeError(
                "File is not an Android bootimg. (" + file_output + ")")

    # Extract all the files using the correct tool.
    if bootimg_is_sonyelf == True:
        pmb.chroot.user(
            args, ["unpackelf", "-i", "boot.img"], working_dir=temp_path)
    else:
        pmb.chroot.user(args, ["unpackbootimg", "-i",
                               "boot.img"], working_dir=temp_path)

    output = {}
    # Get base, offsets, pagesize, cmdline and qcdt info

    # SonyELF images have less info to work with, so let's make a special case
    if bootimg_is_sonyelf == True:
        with open(bootimg_path + "-base", 'r') as f:
            output["base"] = ("0x%08x" % int(f.read().replace('\n', ''), 16))
        with open(bootimg_path + "-kerneloff", 'r') as f:
            output["kernel_offset"] = ("0x%08x" %
                                       int(f.read().replace('\n', ''), 16))
        with open(bootimg_path + "-ramdiskoff", 'r') as f:
            output["ramdisk_offset"] = ("0x%08x" %
                                        int(f.read().replace('\n', ''), 16))
        with open(bootimg_path + "-pagesize", 'r') as f:
            output["pagesize"] = f.read().replace('\n', '')
        with open(bootimg_path + "-cmdline", 'r') as f:
            output["cmdline"] = f.read().replace('\n', '')
        output["sonyelf"] = (
            "true" if bootimg_is_sonyelf == True else "false")
        # Fill these sections w/ dummy data (we don't use them to make the ELF)
        output["second_offset"] = ("0x00000000")
        output["tags_offset"] = ("0x00000000")
        # DTB is appended to kernel, no need to do it here
        output["qcdt"] = ("false")
    else:
        with open(bootimg_path + "-base", 'r') as f:
            output["base"] = ("0x%08x" % int(f.read().replace('\n', ''), 16))
        with open(bootimg_path + "-kernel_offset", 'r') as f:
            output["kernel_offset"] = ("0x%08x" %
                                       int(f.read().replace('\n', ''), 16))
        with open(bootimg_path + "-ramdisk_offset", 'r') as f:
            output["ramdisk_offset"] = ("0x%08x" %
                                        int(f.read().replace('\n', ''), 16))
        with open(bootimg_path + "-second_offset", 'r') as f:
            output["second_offset"] = ("0x%08x" %
                                       int(f.read().replace('\n', ''), 16))
        with open(bootimg_path + "-tags_offset", 'r') as f:
            output["tags_offset"] = ("0x%08x" %
                                     int(f.read().replace('\n', ''), 16))
        with open(bootimg_path + "-pagesize", 'r') as f:
            output["pagesize"] = f.read().replace('\n', '')
        with open(bootimg_path + "-cmdline", 'r') as f:
            output["cmdline"] = f.read().replace('\n', '')
        output["qcdt"] = ("true" if os.path.isfile(bootimg_path + "-dt") and
                          os.path.getsize(bootimg_path + "-dt") > 0 else "false")

    # Cleanup
    pmb.chroot.root(args, ["rm", "-r", temp_path])

    return output
