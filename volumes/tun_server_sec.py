#!/usr/bin/env python3
from collections import defaultdict
import time
import os, fcntl, struct, socket, select, hashlib
from scapy.all import *

SECRET = b"vpn_secret"
authenticated = False
client_addr = None
IP_POOL = defaultdict(bool)  # Tracks assigned IPs
IP_POOL["192.168.53.1"] = True  # Reserve server IP
LEASE_TIME = 3600  # 1 hour lease (adjust as needed)

def assign_ip():
    """Assigns the next available IP in 192.168.53.2-254 range"""
    for i in range(2, 255):
        ip = f"192.168.53.{i}"
        if not IP_POOL[ip]:
            IP_POOL[ip] = time.time() + LEASE_TIME  # Set expiry
            return ip
    return None 

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

client_addr = None
# client_last_seen = None
# TIMEOUT = 10

while True:
    ready, _, _ = select.select([tun, sock], [], [])
    for fd in ready:
        if fd == sock:
            data, client_addr = sock.recvfrom(2048)
            ok, packet = verify_hash(data)

            if not authenticated:
                if packet == b'AUTH:' + SECRET:
                    authenticated = True
                    client_ip = assign_ip()
                    if client_ip:
                        sock.sendto(add_hash(f"ASSIGN_IP:{client_ip}".encode()), client_addr)
                        print(f"✅ Assigned {client_ip} to {client_addr}")
                    else:
                        sock.sendto(add_hash(b"NO_IPS_AVAILABLE"), client_addr)
                    continue

            if ok:
                try:
                    pkt = IP(packet)
                    print("From socket <==", pkt.summary())
                    os.write(tun, packet)
                except Exception as e:
                    print(f"🛑 Failed to parse packet as IP: {e}")
            else:
                print("Packet failed integrity check. Dropped.")


        elif fd == tun:
            packet = os.read(tun, 2048)
            ip = IP(packet)
            print("From TUN ==>", ip.summary())
            if client_addr:
                sock.sendto(add_hash(packet), client_addr)
            else:
                print("Client address unknown. Skipping packet.")

