export DISPLAY=:0

. /etc/deviceinfo

if test -z "${XDG_RUNTIME_DIR}"; then
	export XDG_RUNTIME_DIR=/tmp/12345-runtime-dir
	if ! test -d "${XDG_RUNTIME_DIR}"; then
		mkdir "${XDG_RUNTIME_DIR}"
		chmod 0700 "${XDG_RUNTIME_DIR}"
		chown 12345:12345 "${XDG_RUNTIME_DIR}"
	fi

	if [ $(tty) = "/dev/tty1" ]; then
		udevadm trigger
		udevadm settle

		chown user:user /dev/fb0
		sleep 2
		su user -c 'sh /bin/startkwin.sh'
		sleep 1
	fi
fi
