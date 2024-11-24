import socket

def get_host(ip):
    try:
        return socket.gethostbyaddr(ip)
    except socket.herror:
        return None, None, None

def scan_network():
    for i in range(1, 255):
        ip = f"192.168.1.{i}"
        name, alias, addresslist = get_host(ip)
        if name:
            print(f"{ip} is {name}")

scan_network()
