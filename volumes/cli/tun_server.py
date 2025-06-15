#!/usr/bin/env python3

import os, fcntl, struct, socket, select
from scapy.all import *

# === TUN Setup ===
TUNSETIFF = 0x400454ca
IFF_TUN = 0x0001
IFF_NO_PI = 0x1000

tun = os.open("/dev/net/tun", os.O_RDWR)
ifr = struct.pack('16sH', b'srv%d', IFF_TUN | IFF_NO_PI)
ifname_bytes = fcntl.ioctl(tun, TUNSETIFF, ifr)
ifname = ifname_bytes.decode('UTF-8')[:16].strip('\x00')
print("TUN interface:", ifname)

os.system(f"ip addr add 192.168.53.1/24 dev {ifname}")
os.system(f"ip link set dev {ifname} up")

# === UDP Setup ===
IP_A = "0.0.0.0"
PORT = 9090
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((IP_A, PORT))

client_addr = None

while True:
    ready, _, _ = select.select([tun, sock], [], [])
    for fd in ready:
        if fd == sock:
            data, client_addr = sock.recvfrom(2048)
            pkt = IP(data)
            print("From socket <==", pkt.summary())
            os.write(tun, data)

        elif fd == tun:
            packet = os.read(tun, 2048)
            ip = IP(packet)
            print("From TUN ==>", ip.summary())
            if client_addr:
                sock.sendto(packet, client_addr)
            else:
                print("Client address unknown. Skipping packet.")

