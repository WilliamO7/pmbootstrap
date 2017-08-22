export QT_QPA_PLATFORM=wayland
export QT_QPA_PLATFORMTHEME=KDE
export QT_WAYLAND_DISABLE_WINDOWDECORATION=1
export XDG_CURRENT_DESKTOP=KDE
export KSCREEN_BACKEND=QScreen

export KDE_FULL_SESSION=1
export KDE_SESSION_VERSION=5
export KWIN_COMPOSE=Q

export $(dbus-launch)

ck-launch-session kwin_wayland --framebuffer --xwayland -- /usr/bin/plasmashell -p org.kde.satellite.phone 2> /tmp/kwin_log.txt
