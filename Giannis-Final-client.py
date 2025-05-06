from socket import *
import os

server_ip = '127.0.0.1'
PORT = 12345

client = socket(AF_INET, SOCK_STREAM)
client.connect((server_ip, PORT))

# Send username
username = input("Enter your username: ")
client.send(username.encode())

# Receive welcome or rejection
response = client.recv(1024).decode()
if "username taken " in response:
    print(response)
    client.close()
    exit()
print(response)

# Client command loop
try:
    while True:
        cmd = input(">>> ").strip()
        if cmd == "put":
            filename = input("Enter filename to upload: ")
            if not os.path.exists(filename):
                print("File not found.")
                continue
            client.send("put".encode())
            if client.recv(1024).decode() == "filename":
                client.send(os.path.basename(filename).encode())
                if client.recv(1024).decode() == "reject":
                    print("File already exists.")
                else:
                    with open(filename, 'rb') as f:
                        while chunk := f.read(1024 * 1024):
                            client.sendall(chunk)
                    print("Upload complete.")

        elif cmd.startswith("get "):
            client.send(cmd.encode())
            status = client.recv(1024).decode()
            if status == "sending":
                fname = cmd[4:]
                with open("downloaded_" + fname, 'wb') as f:
                    while True:
                        chunk = client.recv(1024 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)
                print("Download complete.")
            else:
                print("File not found.")

        elif cmd.startswith("stream "):
            client.send(cmd.encode())
            status = client.recv(1024).decode()
            if status == "streaming":
                fname = cmd[7:]
                with open("streamed_" + fname, 'wb') as f:
                    while True:
                        chunk = client.recv(1024 * 64)
                        if b'end_stream' in chunk:
                            break
                        f.write(chunk)
                print("Streaming complete (saved as streamed_" + fname + ")")
            else:
                print("File not found.")

        else:
            client.send(cmd.encode())
            response = client.recv(4096).decode()
            print(response)
            if cmd.lower() == "close":
                break
except:
    pass
finally:
    client.close()
