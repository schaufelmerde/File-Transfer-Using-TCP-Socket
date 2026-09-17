import os
import socket
import sys
import threading

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5555
BUFFER_SIZE = 4096  # 4KB buffer size
SEPARATOR = "<SEPARATOR>"

# several clients can be writing into REC at once, so serialise the bits
# that would otherwise race: creating the directory and picking a filename
rec_lock = threading.Lock()


def receive_header(conn):
    # the header is terminated by a newline, so read one byte at a time
    # until we hit it -- TCP gives us a stream, not discrete messages, so a
    # single recv() could otherwise swallow part of the file contents too
    header = b""
    while not header.endswith(b"\n"):
        byte = conn.recv(1)
        if not byte:
            raise ConnectionError("connection closed before the header arrived")
        header += byte
    return header.decode().rstrip("\n")


def reserve_path(filename):
    # claim a free path under REC so two clients sending the same filename
    # don't write over each other: file.txt, file-1.txt, file-2.txt, ...
    with rec_lock:
        os.makedirs("REC", exist_ok=True)
        stem, ext = os.path.splitext(filename)
        candidate = os.path.join("REC", filename)
        counter = 1
        while os.path.exists(candidate):
            candidate = os.path.join("REC", f"{stem}-{counter}{ext}")
            counter += 1
        # create it now, while we still hold the lock, so the name is taken
        open(candidate, "wb").close()
        return candidate


def receive_file(conn, address):
    received = receive_header(conn)
    filename, filesize = received.split(SEPARATOR)
    filename = os.path.basename(filename)
    filesize = int(filesize)
    file_path = reserve_path(filename)
    remaining = filesize
    with open(file_path, "wb") as f:
        while remaining > 0:
            # read exactly what the header promised, no more -- anything
            # past it belongs to whatever the sender does next
            data = conn.recv(min(BUFFER_SIZE, remaining))
            if not data:
                break
            f.write(data)
            remaining -= len(data)
    if remaining > 0:
        print(f"[!] Incomplete transfer from {address[0]}:{address[1]}: "
              f"{filesize - remaining} of {filesize} bytes saved as {file_path}")
    else:
        print(f"File received from {address[0]}:{address[1]} saved as {file_path}")


def handle_client(conn, address):
    try:
        receive_file(conn, address)
    except (ConnectionError, OSError, ValueError) as e:
        # one malformed transfer shouldn't take the whole server down
        print(f"[!] Transfer from {address[0]}:{address[1]} failed: {e}")
    finally:
        conn.close()


def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if sys.platform == "win32":
        # Windows SO_REUSEADDR lets a second process bind a port that is
        # already in use and quietly steal connections from the first, so
        # ask for the opposite: fail loudly if someone already has it
        s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    else:
        # elsewhere this just avoids a bind error while the old socket
        # lingers in TIME_WAIT after a restart
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind((SERVER_HOST, SERVER_PORT))
    except OSError as e:
        print(f"[X] Could not listen on port {SERVER_PORT}: {e}")
        print("    Is another copy of the server already running?")
        s.close()
        return
    s.listen(5)
    print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")
    try:
        while True:
            conn, address = s.accept()
            print(f"[+] {address[0]}:{address[1]} is connected.")
            # hand the transfer to a worker so accept() is free immediately
            # and slow clients don't block everyone behind them
            thread = threading.Thread(target=handle_client, args=(conn, address))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\n[*] Shutting down.")
    finally:
        s.close()

start_server()
