import socket
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 8002))
    print('OK: Can bind to 8002')
except Exception as e:
    print('ERROR:', e)
