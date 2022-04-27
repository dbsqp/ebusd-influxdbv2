NAS Serial
download
uname -a
Linux nas 3.10.105 #25426 SMP Mon Dec 14 18:45:24 CST 2020 x86_64 GNU/Linux synology_braswell_416play
download complied serial drivers for braswell 416play from jadahl

process
	1.	Install drivers in /lib/modules
	2.	install modules
	3.	create start-up task
Note needs to be repeated after each OS update

CLI commands:
sudo cp /volume1/docker/Serial/cp210x.ko /lib/modules/
sudo chmod 644 /lib/modules/cp210x.ko
sudo insmod /lib/modules/usbserial.ko
sudo insmod /lib/modules/cp210x.ko

create task in synlogy DSM Tascheculer for at startup "start USB serial" "bash /volume1/docker/eBUSd/serial/start-usb-drivers.sh" as root

sudo chmod 666 /dev/ttyUSB0

check if recognised
/dev/ttyUSB0 exists
ls -al /dev/ttyUSB0
crw-rw-rw- 1 root root 188, 0 Jun  2 23:17 ttyUSB0
