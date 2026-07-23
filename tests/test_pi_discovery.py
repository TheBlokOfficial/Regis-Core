import socket
import logging

logging.basicConfig(level=logging.INFO)

DISCOVERY_PORT = 8002
PING_MSG = b"REGIS_DISCOVERY_PING"

def ping_device(ip):
    logging.info(f"Test pingu do: {ip}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(2)
    try:
        sock.sendto(PING_MSG, (ip, DISCOVERY_PORT))
        data, addr = sock.recvfrom(1024)
        logging.info(f"Odebrano od {addr}: {data.decode()}")
        return True
    except socket.timeout:
        logging.error(f"Timeout dla {ip}")
    except Exception as e:
        logging.error(f"Błąd dla {ip}: {e}")
    finally:
        sock.close()
    return False

ping_device("255.255.255.255")
ping_device("192.168.0.255")
ping_device("192.168.0.119")  # Unicast bezpośrednio do malinki
