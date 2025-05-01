from socket import *
from threading import Thread

def receive(sock):
    while True:
        try:
            msg = sock.recv(1024).decode()
            if not msg:
                print("Disconnected from server.")
                break
            print("\n" + msg)
        except:
            print("Disconnected from server.")
            break

def main():
    server_ip = input("Enter server IP: ")
    PORT = 12345

    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((server_ip, PORT))

    # Send username immediately after connecting
    while True:
        name = input("Type your username: ").strip()
        if name:
            client_socket.send(name.encode())
            break
        else:
            print("Username cannot be empty. Please try again.")

    Thread(target=receive, args=(client_socket,), daemon=True).start()

    try:
        while True:
            msg = input()
            if msg.lower() in ("close", "leave"):
                client_socket.send(msg.encode())
                break
            client_socket.send(msg.encode())
    except:
        pass
    finally:
        client_socket.close()

if __name__ == "__main__":
    main()
