from socket import *
from threading import Thread
import time
import os

clients = {}  # {client_socket: username}
PORT = 12345

def handle_client(client_socket):
    username = clients[client_socket]

    welcome_msg = f"Welcome {username}! Type 'list' to see users or 'msg <username> <message>' to message someone."
    client_socket.send(welcome_msg.encode())

    try:
        while True:
            msg = client_socket.recv(1024).decode()
            if not msg:
                break

            if msg.lower() == "list":
                client_list = "\n".join(clients.values())
                client_socket.send(f"Connected clients:\n{client_list}".encode())

            elif msg.startswith("msg"):
                parts = msg.split(" ", 2)
                if len(parts) == 3:
                    target_username, message = parts[1], parts[2]
                    sent = False
                    for sock, user in clients.items():
                        if user == target_username and sock != client_socket:
                            sock.send(f"From {username}: {message}".encode())
                            sent = True
                            break
                    if not sent:
                        client_socket.send("User not found.".encode())
                else:
                    client_socket.send("Invalid format. Use: msg <username> <message>".encode())

            elif msg.lower() in ("close"):
                break
            else:
                client_socket.send("Unknown command.".encode())
    except:
        pass
    finally:
        print(f"{username} disconnected")
        clients.pop(client_socket, None)
        client_socket.close()

def auto_shutdown_timer(duration):
    time.sleep(duration - 10)
    shutdown_msg = "Server will shut down in 10 seconds!"
    print(shutdown_msg)
    for sock in list(clients.keys()):
        try:
            sock.send(shutdown_msg.encode())
        except:
            pass
    time.sleep(10)
    print("Shutting down server now...")
    for sock in list(clients.keys()):
        try:
            sock.close()
        except:
            pass
    os._exit(0)

def main():
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    server_socket.bind(('', PORT))
    server_socket.listen()
    print(f"Server listening on port {PORT}")

    # Start auto shutdown after 120 seconds
    shutdown_seconds = 120
    Thread(target=auto_shutdown_timer, args=(shutdown_seconds,), daemon=True).start()

    while True:
        client_socket, addr = server_socket.accept()
        print(f"New connection from {addr}")

        # Get username immediately
        username = client_socket.recv(1024).decode().strip()

        if username in clients.values():
            client_socket.send("Username already taken. Connection closed.".encode())
            client_socket.close()
            continue

        clients[client_socket] = username
        Thread(target=handle_client, args=(client_socket,), daemon=True).start()

if __name__ == "__main__":
    main()
