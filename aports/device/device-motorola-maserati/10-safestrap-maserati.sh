#!/bin/sh
. /etc/deviceinfo
. ./init_functions.sh

mkdir /ss
mount -t vfat -o uid=1023,gid=1023,fmask=0007,dmask=0007,allow_utime=0020 ${deviceinfo_safestrap_partition} /ss

slot_loc=$(cat /ss/safestrap/active_slot)

if [ "$slot_loc" = "stock" ]; then
	umount /ss
elif [ "$slot_loc" = "safe" ]; then
	umount /ss
else
	# setup loopbacks
	data_partition=$(losetup -f)
	losetup $data_partition /ss/safestrap/$slot_loc/userdata.img
	kpartx -afs $data_partition

	system_partition=$(losetup -f)
	losetup $system_partition /ss/safestrap/$slot_loc/system.img
fi
