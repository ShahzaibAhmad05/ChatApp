import socket
import threading
import sys
from typing import Dict, Tuple
from datetime import datetime
import random

HOST = "127.0.0.1"
PORT = 55555
ENCODING = "utf-8"
BACKLOG = 100
RECV_BUFSIZE = 4096

#colors for usernames
ANSI_COLORS = [
    "\033[91m",  # red
    "\033[92m",  # green
    "\033[93m",  # yellow
    "\033[94m",  # blue
    "\033[95m",  # magenta
    "\033[96m",  # cyan
]
COLOR_DM = "\033[95;1m"  # bold magenta
COLOR_RESET = "\033[0m"

#lock to protect shared state across client threads
clients_lock = threading.Lock()

#dict to keep track of active clients
clients: Dict[str, Tuple[socket.socket, Tuple[str, int]]] = {}


#helper function to assign a random color to a user
def random_ansi_color():
    return random.choice(ANSI_COLORS)


def send_line(conn: socket.socket, line: str) -> None:
    #this helper sends a single line to a client with newline delimiter
    try:
        conn.sendall((line + "\n").encode(ENCODING))
    except Exception:
        pass  #ignore send errors


def broadcast(system_line: str, exclude: str = "") -> None:
    #sends a system or user message to all clients
    with clients_lock:
        for uname, (c, _) in list(clients.items()):
            if uname == exclude:
                continue
            send_line(c, system_line)


def send_private_message(sender: str, recipient: str, message: str, name_color: str) -> None:
    #this routes a private message from sender to recipient and echos confirmation to sender
    with clients_lock:
        if recipient not in clients:
            conn, _ = clients.get(sender, (None, None))
            if conn:
                send_line(conn, f"[error] user '{recipient}' not found")
            return
        rc_conn, _ = clients[recipient]
        sd_conn, _ = clients[sender]

    #show different formatting for sender and recipient
    send_line(
        rc_conn,
        f"{COLOR_DM}DM{COLOR_RESET} from {name_color}{sender}{COLOR_RESET} \n{message}",
    )
    send_line(sd_conn, f"{COLOR_DM}DM{COLOR_RESET} to {recipient} \n{message}")


def handle_client(conn: socket.socket, addr: Tuple[str, int]) -> None:
    #this thread manages registration then message loop for a single client
    username = None
    try:
        send_line(conn, "welcome to the chat server. please enter a unique username: ")
        raw = conn.recv(RECV_BUFSIZE).decode(ENCODING).strip()
        if not raw:
            #extra error handling
            send_line(conn, "[error] empty username not allowed")
            conn.close()
            return
        requested = raw

        with clients_lock:
            if requested in clients:
                send_line(conn, "[error] username already taken, please try again with a different one")
                conn.close()
                return
            username = requested
            clients[username] = (conn, addr)

        send_line(conn, f"[ok] joined as '{username}'. type '/quit' to leave. use '@user message' for private dm.")
        broadcast(f"[notice] {username} has joined the chat", exclude=username)

        #assign a color to the username
        user_color = random_ansi_color()

        #main loop that processes chat lines
        while True:
            data = conn.recv(RECV_BUFSIZE)
            if not data:
                #disconnect
                break
            line = data.decode(ENCODING).rstrip("\n").strip()
            if not line:
                continue

            if line == "/quit":
                #exit
                send_line(conn, "[ok] goodbye")
                break

            if line.startswith("@"):
                parts = line.split(maxsplit=1)
                #unicast -> expected format '@username message'
                if len(parts) < 2:
                    send_line(conn, "[error] private message format: @username")
                    continue
                target = parts[0][1:]
                if not target:
                    send_line(conn, "[error] missing recipient username after '@'")
                    continue
                msg = parts[1]
                send_private_message(username, target, msg, user_color)
            else:
                #broadcast to all clients including sender
                timestamp = datetime.now().strftime("%I:%M%p").lstrip("0")
                broadcast(f"{user_color}{username}{COLOR_RESET} at {timestamp} \n{line}")
    except ConnectionResetError:
        #sudden client drop
        pass
    except Exception as e:
        try:
            send_line(conn, f"[error] server exception: {e}")
        except Exception:
            pass
    finally:
        #cleanup on client disconnect
        if username:
            with clients_lock:
                if username in clients:
                    try:
                        conn.shutdown(socket.SHUT_RDWR)
                    except Exception:
                        pass
                    try:
                        conn.close()
                    except Exception:
                        pass
                    del clients[username]
            broadcast(f"[notice] {username} has left the chat")


#main function for serving clients
def serve(host: str = HOST, port: int = PORT) -> None:
    #starts the tcp server and accepts new clients
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #allows quick restart avoiding the address already in use
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(BACKLOG)
    print(f"[server] listening on {host}:{port}")

    try:
        while True:
            conn, addr = srv.accept()
            print(f"[server] new connection from {addr}")
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("\n[server] shutting down...")
    finally:
        with clients_lock:
            for uname, (c, _) in list(clients.items()):
                try:
                    send_line(c, "[notice] server is shutting down")
                    c.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    c.close()
                except Exception:
                    pass
            clients.clear()
        try:
            srv.close()
        except Exception:
            pass
        print("[server] closed")


if __name__ == "__main__":
    #optional cli args for host and port
    if len(sys.argv) >= 2:
        HOST = sys.argv[1]
    if len(sys.argv) >= 3:
        PORT = int(sys.argv[2])
    serve(HOST, PORT)
