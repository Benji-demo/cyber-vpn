#!/usr/bin/env python3

import os, fcntl, struct, socket, select
from scapy.all import *

# === TUN Setup ===
TUNSETIFF = 0x400454ca
IFF_TUN = 0x0001
IFF_NO_PI = 0x1000

tun = os.open("/dev/net/tun", os.O_RDWR)
ifr = struct.pack('16sH', b'bini%d', IFF_TUN | IFF_NO_PI)
ifname_bytes = fcntl.ioctl(tun, TUNSETIFF, ifr)
ifname = ifname_bytes.decode('UTF-8')[:16].strip('\x00')
print("TUN interface:", ifname)

os.system(f"ip addr add 192.168.53.99/24 dev {ifname}")
os.system(f"ip link set dev {ifname} up")
os.system(f"ip route add 192.168.60.0/24 dev {ifname}")

# === UDP Setup ===
SERVER_IP = "10.9.0.11"
SERVER_PORT = 9090
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# === Select loop ===
while True:
    ready, _, _ = select.select([tun, sock], [], [])
    for fd in ready:
        if fd == tun:
            packet = os.read(tun, 2048)
            ip = IP(packet)
            print("From TUN ==>", ip.summary())
            sock.sendto(packet, (SERVER_IP, SERVER_PORT))

        elif fd == sock:
            data, _ = sock.recvfrom(2048)
            ip = IP(data)
            print("From socket <==", ip.summary())
            os.write(tun, data)

