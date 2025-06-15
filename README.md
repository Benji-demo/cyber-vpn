# 🚀 VPN Tunnel Lab – Quick Run Guide

## 🛠️ Build and Start

```bash
docker-compose build
docker-compose up -d
```

## Install needed stuff for GUI
```bash
# Create a virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Now install packages
pip install PyQt5 scapy requests
```


## Enter Containers
- use multiple terminal and enter then run
```bash
docker exec -it client-10.9.0.5 /bin/bash        # VPN Client
docker exec -it server-router /bin/bash          # VPN Server
docker exec -it host-192.168.60.5 /bin/bash      # Host V (for telnet)
```
## Run
```bash
chmod +x tun_server.py
sudo ./tun_server.py
```
```bash
chmod +x tun_client.py
sudo ./tun_client.py
```

- then try ping-ing this from the vpn client side
```bash
ping 192.168.60.5 # Pc on internal network
ping 192.168.53.1 # vpn server
```
If this works then the vpn is doing a proper tunnuling

### This is for the attacker scenario
- do
```bash
ip link show
```
- look for one that starts with br - xxxxxxxxxxx
- then do this ( * packet sniffing *)
```bash
sudo tcpdump -i br -66fc5.....(the one from above) -n -A port 9090 
```

- Then telnet to this ip(192.168.60.5) from client vpn and login
```bash
telnet 192.168.60.5
# Login: seed
# Password: dees
```
- You will be able to see the udp packages get sniffed on the * packet sniffing *
