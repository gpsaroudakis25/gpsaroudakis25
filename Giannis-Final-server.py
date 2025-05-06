from socket import *
from threading import Thread
import time
import os
import pickle

clients = {}           # {socket: username}
fileStorage = {}       # {filename: uploader}
PORT = 12345
FILE_DIR = 'videos/'   # Folder to store uploaded files

os.makedirs(FILE_DIR, exist_ok=True)

# Handles messages and commands from a single client
def handle_client(client_socket):
    username = clients[client_socket]
    welcome_msg = f"Welcome {username}! Commands:\n - list\n - msg <username> <message>\n - put\n - listfiles\n - get <filename>\n - stream <filename>\n - close"
    client_socket.send(welcome_msg.encode())

    try:
        while True:
            msg = client_socket.recv(1024).decode()
            if not msg:
                break

            # Show list of connected usernames
            if msg.lower() == "list":
                users = "\n".join(clients.values())
                client_socket.send(f"Connected users:\n{users}".encode())

            # Send private message
            elif msg.startswith("msg"):
                parts = msg.split(" ", 2)
                if len(parts) == 3:
                    target, message = parts[1], parts[2]
                    sent = False
                    for sock, user in clients.items():
                        if user == target and sock != client_socket:
                            sock.send(f"[{username}] → You: {message}".encode())
                            sent = True
                            break
                    if not sent:
                        client_socket.send("User not found.".encode())
                else:
                    client_socket.send("Use: msg <username> <message>".encode())

            # Upload file to server
            elif msg.lower() == "put":
                client_socket.send("filename".encode())
                filename = client_socket.recv(1024).decode()
                fullpath = FILE_DIR + filename
                if filename in fileStorage:
                    client_socket.send("reject".encode())
                else:
                    client_socket.send("ready".encode())
                    with open(fullpath, 'wb') as f:
                        while True:
                            chunk = client_socket.recv(1024 * 1024)
                            if not chunk:
                                break
                            f.write(chunk)
                            if len(chunk) < 1024 * 1024:
                                break
                    fileStorage[filename] = username
                    print(f"{username} uploaded {filename}")

            # List available files
            elif msg.lower() == "listfiles":
                if fileStorage:
                    files = "\n".join([f"{f} (by {u})" for f, u in fileStorage.items()])
                    client_socket.send(files.encode())
                else:
                    client_socket.send("No files available.".encode())

            # Download a file
            elif msg.startswith("get "):
                filename = msg[4:].strip()
                fullpath = FILE_DIR + filename
                if os.path.exists(fullpath):
                    client_socket.send("sending".encode())
                    with open(fullpath, 'rb') as f:
                        while chunk := f.read(1024 * 1024):
                            client_socket.sendall(chunk)
                    print(f"{username} downloaded {filename}")
                else:
                    client_socket.send("not found".encode())

            # Stream a file
            elif msg.startswith("stream "):
                filename = msg[7:].strip()
                fullpath = FILE_DIR + filename
                if os.path.exists(fullpath):
                    client_socket.send("streaming".encode())
                    with open(fullpath, 'rb') as f:
                        while chunk := f.read(1024 * 64):  # smaller chunk for streaming
                            client_socket.sendall(chunk)
                    client_socket.send(b'end_stream')
                    print(f"{username} streamed {filename}")
                else:
                    client_socket.send("not found".encode())

            # Disconnect client
            elif msg.lower() == "close":
                break
            else:
                client_socket.send("Unknown command.".encode())
    except:
        pass
    finally:
        print(f"{username} disconnected")
        clients.pop(client_socket, None)
        client_socket.close()

# Sends shutdown warning then closes all connections
def auto_shutdown_timer(seconds):
    time.sleep(seconds - 10)
    warning = "Server shutting down in 10 seconds!"
    print(warning)
    for sock in list(clients.keys()):
        try:
            sock.send(warning.encode())
        except:
            pass
    time.sleep(10)
    print("Server is now closed.")
    for sock in list(clients.keys()):
        try:
            sock.close()
        except:
            pass
    os._exit(0)

# Main function to start server
def main():
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    server_socket.bind(('', PORT))
    server_socket.listen()
    print(f" Server running on port {PORT}")

    Thread(target=auto_shutdown_timer, args=(120,), daemon=True).start()

    while True:
        client_socket, addr = server_socket.accept()
        try:
            username = client_socket.recv(1024).decode().strip()
            if username in clients.values():
                client_socket.send("Username taken. Disconnecting.".encode())
                client_socket.close()
                continue
            clients[client_socket] = username
            print(f"{username} connected")
            Thread(target=handle_client, args=(client_socket,), daemon=True).start()
        except:
            client_socket.close()

if __name__ == "__main__":
    main()

