import socket

HOST = '192.168.217.79'  # your Pi's IP
PORT = 9090

while True:
    cmd = input("> ")
    if not cmd:
        break
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(cmd.encode() + b"\n")
        data = s.recv(1024)
        print("Response:", data.decode().strip())
