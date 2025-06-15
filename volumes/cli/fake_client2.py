#!/usr/bin/env python3

import socket
import hashlib

WRONG_SECRET = b"wrong_password"
SERVER_IP = "10.9.0.11"
SERVER_PORT = 9090

def add_hash(packet, secret):
    h = hashlib.sha256(secret + packet).digest()
    return packet + h

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Attempt authentication with wrong password
auth_msg = b'AUTH:' + WRONG_SECRET
sock.sendto(add_hash(auth_msg, WRONG_SECRET), (SERVER_IP, SERVER_PORT))
print("🚨 Sent invalid authentication attempt")
