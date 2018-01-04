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

def check_sonyelf(file_output):
    start = "ELF "
    end = "-bit LSB executable, ARM"
    return file_output.startswith(start) and file_output.output.endswith(end)

def bootimg_parse_field(bootimg_path, field, bootimg_is_sonyelf):
    """
    Get the content for one deviceinfo variable out of the extracted boot.img.

    :param bootimg_path: absolute path to the boot.img file, with the extracted files in the same
                         folder
    :param field: deviceinfo field we're interested in, without the "deviceinfo_flash" prefix.
    """

    # Hex numbers
    if field in ["base", "kernel_offset", "ramdisk_offset", "second_offset", "tags_offset"]:
        with open(bootimg_path + "-" + field, "r") as handle:
            return "0x%08x" % int(handle.read().replace('\n', ''), 16)

    # Strings
    if field in ["pagesize", "cmdline"]:
        with open(bootimg_path + "-" + field, "r") as handle:
            return handle.read().replace('\n', '')

    # qcdt: Check for a non-empty "boot.img-dt" file
    if field == "qcdt":
        if os.path.isfile(bootimg_path + "-dt") and os.path.getsize(bootimg_path + "-dt") > 0:
            return "true"
        return "false"
        
    # sonyelf: check if the relevant flag has been set by the below function
    if field == "sonyelf":
        if bootimg_is_sonyelf:
            return "true"
        return "false"

    raise RuntimeError("bootimg_parse_field: Don't know how to parse '" + field + "'!")

def bootimg(args, path):
    bootimg_is_sonyelf = False
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
        elif check_sonyelf(file_output):
            bootimg_is_sonyelf = True
            # We have a Sony Xperia ELF format boot image, which some devices
            # (such as the Xperia J) have. We need special tools to deal with these,
            # namely unpackelf to get the required offsets.
            pmb.chroot.apk.install(args, ["file", "unpackelf"])
        else:
            raise RuntimeError(
                "File is not an Android bootimg. (" + file_output + ")")

    # Extract all the files using the correct tool.
    if bootimg_is_sonyelf:
        pmb.chroot.user(args, ["unpackelf", "-i", "boot.img"], working_dir=temp_path)
    else:
        pmb.chroot.user(args, ["unpackbootimg", "-i", "boot.img"], working_dir=temp_path)

    output = {}
    # Get base, offsets, pagesize, cmdline and qcdt info
    # Necessary fields
    fields = ["base", "kernel_offset", "ramdisk_offset", "pagesize", "cmdline"]
    if not bootimg_is_sonyelf:
        fields += ["second_offset", "tags_offset"]

    # Parse fields from extracted files
    ret = {"generate_bootimg": "true"}
    for field in fields:
        ret[field] = bootimg_parse_field(bootimg_path, field, bootimg_is_sonyelf)
    return ret

    # Cleanup
    pmb.chroot.root(args, ["rm", "-r", temp_path])

    return output
