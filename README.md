TCP Socket File Transfer using Python
=====================================

This repository contains a simple file transfer application using TCP sockets in Python. It consists of a server and a client that let you send files between two machines on the same network, in either direction.

Prerequisites
-------------

* **To receive files:** any Python 3. `server.py` uses only the standard library.
* **To send files:** Python 3.8 - 3.13, because the client needs PyQt5, which has
  no wheels for Python 3.14 yet.

Quick start (Windows)
---------------------

Three batch files handle the setup. Run them by double-clicking.

| File | What it does |
| --- | --- |
| `setup.bat` | Creates a virtual environment and installs PyQt5 and tqdm. Needed only on a machine that will **send** files. Safe to re-run. |
| `run-server.bat` | Starts the server so this machine can **receive**. Prints this machine's IP address and warns if the firewall port looks closed. Needs no setup — it falls back to the system Python. |
| `run-client.bat` | Opens the client window so this machine can **send**. |

Sending in both directions
--------------------------

To move files freely between two machines, run **`run-server.bat` on both of them**
and leave it running. Each machine is then a receiver, and either one can send to
the other with `run-client.bat`. The server accepts connections from any address,
so no extra configuration is needed.

On each machine, once:

1. Run `setup.bat` (only needed for sending).
2. Allow port 5555 through the firewall. In an **Administrator** PowerShell:

    ```powershell
    New-NetFirewallRule -DisplayName "TCP File Transfer" -Direction Inbound -LocalPort 5555 -Protocol TCP -Action Allow
    ```

    Windows may instead show a "Windows Defender Firewall has blocked some
    features" prompt the first time the server runs; allowing it on **Private
    networks** does the same thing. On Linux with ufw: `sudo ufw allow 5555/tcp`.
    To undo it later: `Remove-NetFirewallRule -DisplayName "TCP File Transfer"`.

Then, whenever you want to transfer:

1. Run `run-server.bat` on **both** machines. Each window prints its own IP address,
   something like `192.168.1.42`.
2. On the machine you are sending *from*, run `run-client.bat`.
3. Type the **other** machine's IP into the **Server IP** box, leave the port at
   `5555`, click **Choose File**, then **Send File**.
4. The file lands in the `REC` folder next to `server.py` on the receiving machine.

Send the other way by doing steps 2-3 on the other machine. Both servers stay
running, so neither side needs restarting to reverse direction.

Manual setup (any platform)
---------------------------

If you are not on Windows, or prefer not to use the batch files:

```shell
python3 -m venv .venv
.venv/bin/python -m pip install pyqt5 tqdm      # sending machines only
.venv/bin/python server.py                      # to receive
.venv/bin/python client.py                      # to send
```

On a machine that only receives, skip the virtual environment entirely and run
`python3 server.py`.

<details>
<summary>Alternative: using pipenv</summary>

```shell
pip install pipenv
pipenv install
pipenv shell
```

This uses the `Pipfile`, which pins Python 3.11.

</details>

How it behaves
--------------

The server listens on `0.0.0.0:5555`, accepting connections on any network
interface. Received files are saved to `./REC`, created if it does not exist.

Each client is handled in its own thread, so several transfers can run at once and
a slow sender does not hold up the others. If two files arrive with the same name,
the later ones are saved as `name-1.ext`, `name-2.ext`, and so on, rather than
overwriting. A failed or malformed transfer is logged and the server keeps running.
Press Ctrl+C to stop it.

The client shows transfer progress in its console window, and reports the outcome
in a dialog.

Troubleshooting
---------------

| Symptom | Likely cause |
| --- | --- |
| Dialog says the connection timed out | Firewall on the receiving machine is blocking port 5555 (see the firewall step above), or the two machines are not on the same network |
| Dialog says the connection was actively refused | The server isn't running on the receiving machine, or you typed the wrong port |
| Wrong machine receives nothing | IP address typo, or you took the IP of the wrong adapter — check `ipconfig` again |
| `ModuleNotFoundError: No module named 'PyQt5'` | Run `setup.bat` on that machine, or activate the virtual environment first |
| Both machines on Wi-Fi but cannot connect | Some networks (guest Wi-Fi, public hotspots) isolate clients from each other. Try a different network or a wired connection |

Notes and limitations
---------------------

* **Transfers are not encrypted or authenticated.** Anything sent travels over the network in plain text, and the server accepts a file from anyone who can reach the port. Use this on networks you trust, and stop the server when you are done with it.
* Both machines must be on the same local network. This is not designed to work across the internet.
* A single connection only moves a file one way, from client to server. Run the
  server on both machines to transfer in either direction.

Protocol
--------

The client opens a TCP connection and sends a newline-terminated header:

```
<filename><SEPARATOR><filesize>\n
```

followed by exactly `filesize` bytes of file content. The server reads up to the newline to find the header boundary, then reads exactly that many bytes. The newline matters: TCP is a byte stream with no message boundaries, so without a delimiter the header and the start of the file can arrive in the same packet and be read together.

Contributing
------------

Contributions are welcome! If you have any suggestions, improvements, or bug fixes, please open an issue or a pull request.

License
-------

This project is licensed under the [MIT License](LICENSE).

Acknowledgements
----------------

This project was inspired by the need for a simple file transfer mechanism using TCP sockets in Python. Special thanks to the developers of PyQt5 and tqdm for their excellent libraries.
