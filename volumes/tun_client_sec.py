#!/usr/bin/env python3

import os, fcntl, struct, socket, select,hashlib, sys, atexit
from scapy.all import *

SECRET = sys.argv[1].encode() if len(sys.argv) > 1 else b"defaultpass" # Shared secret for auth + integrity(bad practice to have hard coded secret)
authenticated = False   # To track auth state (on server)

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
ifr = struct.pack('16sH', b'bini%d', IFF_TUN | IFF_NO_PI)
ifname_bytes = fcntl.ioctl(tun, TUNSETIFF, ifr)
ifname = ifname_bytes.decode('UTF-8')[:16].strip('\x00')
with open("/tmp/vpn_ifname", "w") as f:
    f.write(ifname)
atexit.register(lambda: os.path.exists("/tmp/vpn_ifname") and os.remove("/tmp/vpn_ifname"))
print("TUN interface:", ifname)

os.system(f"ip addr add 192.168.53.99/24 dev {ifname}")
os.system(f"ip link set dev {ifname} up")
os.system(f"ip route add 192.168.60.0/24 dev {ifname}")

# === UDP Setup ===
SERVER_IP = "10.9.0.11"
SERVER_PORT = 9090
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Authenticate once at startup
auth_msg = b'AUTH:' + SECRET
sock.sendto(add_hash(auth_msg), (SERVER_IP, SERVER_PORT))
print("🔐 Sent authentication packet")
with open("/tmp/vpn_connected", "w") as f:
    f.write("ok")
atexit.register(lambda: os.path.exists("/tmp/vpn_connected") and os.remove("/tmp/vpn_connected"))

# === Select loop ===
while True:
    ready, _, _ = select.select([tun, sock], [], [])
    for fd in ready:
        if fd == tun:
            packet = os.read(tun, 2048)
            ip = IP(packet)
            print("From TUN ==>", ip.summary())
            sock.sendto(add_hash(packet), (SERVER_IP, SERVER_PORT))

        elif fd == sock:
            data, _ = sock.recvfrom(2048)
            ok, packet = verify_hash(data)
            if ok:
                ip = IP(packet)
                print("From socket <==", ip.summary())
                os.write(tun, packet)
            else:
                print("Packet failed integrity check. Dropped.")
