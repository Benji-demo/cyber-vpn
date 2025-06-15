#!/usr/bin/env python3
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.sendto(b"Wrong passwork or another pass", ("10.9.0.11", 9090))