import socket
import threading
import os
import msvcrt
import keyboard
import time


ENCODING = "utf-8"
RECV_BUFSIZE = 4096
USERNAME = ""
CHAT_PAUSE_FLAG = False       #global flag to signal receiver thread to stop
RUNNING_FLAG = True
chatHistory = []


def recv_loop(conn: socket.socket) -> None:
    #this thread continuously prints incoming lines until stop is requested
    global CHAT_PAUSE_FLAG, RUNNING_FLAG, USERNAME
    try:
        while RUNNING_FLAG:
            data = conn.recv(RECV_BUFSIZE)
            if not data:
                print("[info] connection closed by server")
                break
            recv_msg = data.decode(ENCODING)
            #if the msg is from the current user, mention (You)
            if USERNAME in recv_msg.splitlines()[0]:
                recv_msg = recv_msg.replace(USERNAME, USERNAME + " (You)", 1)
            else:   #if the msg is not the user's own
                print(recv_msg)
            chatHistory.append(recv_msg)

    except Exception:
        print("[error] receive loop ended unexpectedly")
    finally:
        RUNNING_FLAG = False


def printChat():
    global chatHistory
    os.system("cls")
    print("------------------------- Chat -------------------------")
    print("--------------------------------------------------------")
    print("tip: press 'a' to type a message")
    print("tip: press 'esc' to exit")
    print("--------------------------------------------------------")
    print()
    for lines in chatHistory:
        print(lines)


def typeMode():
    """ returns an empty string if no input else returns input """
    global CHAT_PAUSE_FLAG
    CHAT_PAUSE_FLAG = True
    os.system("cls")
    print("-------------------- Type a Message --------------------")
    print("--------------------------------------------------------")
    print("tip: type a message and press enter to send")
    print("tip: use private dm with @username at the beginning (case-sensitive)")
    print("tip: press 'esc' to discard")
    print("--------------------------------------------------------")
    print()
    print("> ", end="", flush=True)

    buf = ""
    while msvcrt.kbhit():       #drain any stored input
        msvcrt.getwch()
    while RUNNING_FLAG:
        ch = msvcrt.getwch()
        if ch == "\r" or ch == "\n":     #enter
            CHAT_PAUSE_FLAG = False
            return buf
        elif ch == "\x1b":               #esc
            CHAT_PAUSE_FLAG = False
            return ""
        elif ch == "\b":                 #backspace
            if buf:
                buf = buf[:-1]
                print("\b \b", end="", flush=True)
        else:
            buf += ch
            print(ch, end="", flush=True)


def main():
    global USERNAME
    #set values for the local host and port
    host, port = "127.0.0.1", 55555

    print("[proc] connecting to chat server...")
    #establish a tcp connection
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
    except Exception as e:
        print(f"[error] could not connect: {e}")
        return

    try:        #print initial server greeting
        greeting = sock.recv(RECV_BUFSIZE).decode(ENCODING).strip()
        if greeting:
            print(greeting)
    except Exception:
        print("[error] failed to receive greeting")
        sock.close()
        return

    #get the username
    USERNAME = input("\nEnter username (without spaces): ").strip()
    if not USERNAME:
        print("[error] empty username not allowed")
        sock.close()
        return
    if len(USERNAME.split()) != 1:
        print("[error] username cannot contain spaces")
        sock.close()
        return
    try:
        sock.sendall((USERNAME + "\n").encode(ENCODING))
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
    t = threading.Thread(target=recv_loop, args=(sock,), daemon=True)
    t.start()

    printChat()
    try:
        while RUNNING_FLAG:
            if msvcrt.kbhit():
                    ch = msvcrt.getwch()
        
                    if ch.lower() == 'a':   # 'a' key to type a message
                        userInput = typeMode()
                        if userInput:
                            try:
                                sock.sendall((userInput + "\n").encode(ENCODING))
                            except BrokenPipeError:
                                print("[error] server closed the connection")
                                break
                        printChat()         #show chat again

                    elif ch == '\x1b':  # ESC
                        os.system("cls")
                        if input("Do you want to exit? (y) ") in ["y", "Y"]:
                            break
                        else:
                            printChat()     #show chat again

            time.sleep(0.01)     #sleep for 10ms

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
        CHAT_PAUSE_FLAG = True


if __name__ == "__main__":
    main()
