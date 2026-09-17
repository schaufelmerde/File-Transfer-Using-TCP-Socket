import os
import socket
import sys
import threading

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5555
BUFFER_SIZE = 4096  # 4KB buffer size
SEPARATOR = "<SEPARATOR>"
REC_DIR = "REC"

# several clients can be writing into REC at once, so serialise the bits
# that would otherwise race: creating directories and picking a filename
rec_lock = threading.Lock()


def receive_header(conn):
    # the header is terminated by a newline, so read one byte at a time
    # until we hit it -- TCP gives us a stream, not discrete messages, so a
    # single recv() could otherwise swallow part of the file contents too.
    # returns None when the client has cleanly finished sending.
    header = b""
    while not header.endswith(b"\n"):
        byte = conn.recv(1)
        if not byte:
            if not header:
                return None
            raise ConnectionError("connection closed part-way through a header")
        header += byte
    return header.decode().rstrip("\n")


def safe_parts(raw):
    # a sender supplies the relative path, so treat it as hostile: strip
    # anything that could climb out of REC or name an absolute location
    parts = []
    for part in raw.replace("\\", "/").split("/"):
        part = part.strip().rstrip(".")
        if part in ("", ".", ".."):
            continue
        if ":" in part:
            # drive or stream qualifiers like C: or name:stream
            part = part.split(":")[-1]
        if part:
            parts.append(part)
    if not parts:
        raise ValueError(f"unusable path {raw!r}")
    return parts


def reserve_path(parts):
    # claim a free path under REC so two senders don't write over each
    # other: file.txt, file-1.txt, file-2.txt, ...
    with rec_lock:
        rec_root = os.path.abspath(REC_DIR)
        directory = os.path.join(rec_root, *parts[:-1])
        os.makedirs(directory, exist_ok=True)

        # belt and braces: refuse anything that still escapes REC
        if os.path.commonpath([rec_root, os.path.abspath(directory)]) != rec_root:
            raise ValueError(f"path escapes {REC_DIR}: {parts}")

        stem, ext = os.path.splitext(parts[-1])
        candidate = os.path.join(directory, parts[-1])
        counter = 1
        while os.path.exists(candidate):
            candidate = os.path.join(directory, f"{stem}-{counter}{ext}")
            counter += 1
        # create it now, while we still hold the lock, so the name is taken
        open(candidate, "wb").close()
        return candidate


def receive_one_file(conn, header):
    relpath, filesize = header.rsplit(SEPARATOR, 1)
    filesize = int(filesize)
    file_path = reserve_path(safe_parts(relpath))
    remaining = filesize
    with open(file_path, "wb") as f:
        while remaining > 0:
            # read exactly what the header promised, no more -- anything
            # past it is the next file in this batch
            data = conn.recv(min(BUFFER_SIZE, remaining))
            if not data:
                break
            f.write(data)
            remaining -= len(data)
    if remaining > 0:
        raise ConnectionError(
            f"only {filesize - remaining} of {filesize} bytes arrived for {relpath}")
    return file_path, filesize


def receive_batch(conn, address):
    # one connection carries any number of files, so a folder of 5000 files
    # doesn't mean 5000 connections
    count = 0
    total = 0
    while True:
        header = receive_header(conn)
        if header is None:
            break
        file_path, filesize = receive_one_file(conn, header)
        count += 1
        total += filesize
        shown = os.path.relpath(file_path, os.path.abspath(REC_DIR))
        print(f"    {shown}  ({filesize} bytes)")
    if count:
        print(f"[+] {count} file(s), {total} bytes from {address[0]}:{address[1]}")
    else:
        print(f"[*] {address[0]}:{address[1]} sent nothing.")


def handle_client(conn, address):
    try:
        receive_batch(conn, address)
    except (ConnectionError, OSError, ValueError) as e:
        # one bad transfer shouldn't take the whole server down
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
