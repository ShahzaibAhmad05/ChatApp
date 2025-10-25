import socket
import threading
import sys
import queue
import os

ENCODING = "utf-8"
RECV_BUFSIZE = 4096


def recv_loop(conn: socket.socket, stop_q: queue.Queue) -> None:
    #this thread continuously prints incoming lines until stop is requested
    try:
        while stop_q.empty():
            data = conn.recv(RECV_BUFSIZE)
            if not data:
                print("[info] connection closed by server")
                break
            for line in data.decode(ENCODING).splitlines():
                if line.strip():
                    print(line)
            print() #print a newline after messages
    except Exception:
        print("[error] receive loop ended unexpectedly")
    finally:
        try:
            stop_q.put_nowait(True)
        except Exception:
            pass


def main():
    #set values for the local host and port
    host, port = "127.0.0.1", 55555

    print("[proc] connecting to chat server...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
    except Exception as e:
        print(f"[error] could not connect: {e}")
        return

    try:        #print initial server greeting and send username
        greeting = sock.recv(RECV_BUFSIZE).decode(ENCODING).strip()
        if greeting:
            print(greeting)
    except Exception:
        print("[error] failed to receive greeting")
        sock.close()
        return

    username = input("\nUsername: ").strip()
    if not username:
        print("[error] empty username not allowed")
        sock.close()
        return
    try:
        sock.sendall((username + "\n").encode(ENCODING))
    except Exception as e:
        print(f"[error] failed to send username: {e}")
        sock.close()
        return

    try:        #read server response
        response = sock.recv(RECV_BUFSIZE).decode(ENCODING).strip()
        if response.startswith("[error]"):
            print(response)
            sock.close()
            return
        print(response)
    except Exception:
        print("[error] username response failed")
        sock.close()
        return

    #start receiver thread
    stop_q: queue.Queue = queue.Queue()
    t = threading.Thread(target=recv_loop, args=(sock, stop_q), daemon=True)
    t.start()

    os.system("cls")
    print("------------------------- Chat -------------------------")
    print("--------------------------------------------------------")
    print()
    print("tip: type messages and press enter to chat")
    print("tip: use private dm with @username")
    print("tip: type '/quit' to leave")
    print()
    print("--------------------------------------------------------")
    print()
    try:
        while stop_q.empty():
            try:
                line = input()
                print("\033[1A\033[2K\033[1A")  #clear the input line
            except EOFError:
                line = "/quit"
            line = (line or "").strip()
            if not line:
                continue
            try:
                sock.sendall((line + "\n").encode(ENCODING))
            except BrokenPipeError:
                print("[error] server closed the connection")
                break
            if line == "/quit":
                break
    except KeyboardInterrupt:
        print("\n[info] interrupted, quitting...")
        try:
            sock.sendall(("/quit\n").encode(ENCODING))
        except Exception:
            pass
    finally:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        sock.close()
        try:
            stop_q.put_nowait(True)
        except Exception:
            pass


if __name__ == "__main__":
    main()
