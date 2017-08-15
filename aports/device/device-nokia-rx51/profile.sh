#!/bin/sh

# Reinsert the wireless driver so udev picks it up
rmmod wl1251_spi && modprobe wl1251_spi
