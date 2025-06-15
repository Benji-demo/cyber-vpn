#!/usr/bin/env python3

import os, fcntl, struct, socket, select, hashlib
from scapy.all import *

SECRET = b"vpn_secret"
authenticated = False
client_addr = None

def add_hash(packet):
    h = hashlib.sha256(SECRET + packet).digest()
    return packet + h

def verify_hash(data):
    if len(data) < 32:
        return False, b''
    packet, recv_hash = data[:-32], data[-32:]
    calc_hash = hashlib.sha256(SECRET + packet).digest()
    return (recv_hash == calc_hash), packet

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

while True:
    ready, _, _ = select.select([tun, sock], [], [])
    for fd in ready:
        if fd == sock:
            try:
                data, addr = sock.recvfrom(2048)
                ok, packet = verify_hash(data)

                if not authenticated:
                    if packet == b'AUTH:' + SECRET:
                        print(f"✅ Client authenticated from {addr}")
                        authenticated = True
                        client_addr = addr
                        continue
                    else:
                        print("❌ Auth failed. Dropping packet.")
                        continue

                if not ok:
                    print("Packet failed integrity check. Dropped.")
                    continue

                if len(packet) < 20:
                    print("❌ Packet too short to be valid IP — dropped.")
                    continue

                try:
                    pkt = IP(packet)
                    print("From socket <==", pkt.summary())
                    os.write(tun, packet)
                except Exception as e:
                    print(f"❌ Packet parsing failed: {e}")
                    continue

            except Exception as e:
                print(f"❌ Error receiving or handling packet: {e}")
                continue

        elif fd == tun:
            packet = os.read(tun, 2048)
            ip = IP(packet)
            print("From TUN ==>", ip.summary())
            if client_addr:
                sock.sendto(add_hash(packet), client_addr)
            else:
                print("Client address unknown. Skipping packet.")
