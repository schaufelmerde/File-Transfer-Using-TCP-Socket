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

Double-click **`run.bat`**. That is all you need: it installs the dependencies on
first run, starts the server if one is not already running, and opens the client.

| File | What it does |
| --- | --- |
| **`run.bat`** | **The one to use.** Does the setup, the server and the client in one go. |
| `setup.bat` | Creates a virtual environment and installs PyQt5 and tqdm. Run by `run.bat` automatically. Safe to re-run. |
| `run-server.bat` | Starts only the server, if you want a receive-only machine. Prints this machine's IP and warns if the firewall port looks closed. Needs no setup — it falls back to the system Python. |
| `run-client.bat` | Opens only the client. |

Sending in both directions
--------------------------

Run **`run.bat` on both machines**. Each one then has a server window listening and
a client window ready, so either machine can send to the other at any time. The
server accepts connections from any address, so there is nothing else to configure.

Keep the server window open — that is what receives. The client window is only
needed while you are sending, and you can close it in between.

On each machine, once:

1. Allow port 5555 through the firewall. In an **Administrator** PowerShell:

    ```powershell
    New-NetFirewallRule -DisplayName "TCP File Transfer" -Direction Inbound -LocalPort 5555 -Protocol TCP -Action Allow
    ```

    Windows may instead show a "Windows Defender Firewall has blocked some
    features" prompt the first time the server runs; allowing it on **Private
    networks** does the same thing. On Linux with ufw: `sudo ufw allow 5555/tcp`.
    To undo it later: `Remove-NetFirewallRule -DisplayName "TCP File Transfer"`.
    Dependencies are installed by `run.bat` itself, so there is no separate
    install step.

Then, to transfer:

1. Run `run.bat` on **both** machines. Each server window prints its own IP address,
   something like `192.168.1.42`.
2. In the client window on the machine you are sending *from*, type the **other**
   machine's IP into the **Server IP** box and leave the port at `5555`.
3. Build the list of what to send:
   * **Add Files...** picks one or more files at once.
   * **Add Folder...** adds a whole folder, including every sub-folder inside it.
     The native folder dialog only takes one at a time, so press it again for each
     extra folder.
   * **Remove Selected** and **Clear** fix up the list.
4. Click **Send**. The progress bar tracks the files as they go.
5. Everything lands in the `REC` folder next to `server.py` on the receiving machine.

To send the other way, do steps 2-4 on the other machine instead. Both servers stay
running, so nothing needs restarting to reverse direction.

Running `run.bat` again when a server is already listening will not start a second
one; it just opens another client.

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

Folders keep their structure: sending `C:\pics\holiday` produces `REC/holiday/...`
with every sub-folder inside it. A batch of files and folders travels over a single
connection, and the server prints each file as it arrives plus a total at the end.

Each client is handled in its own thread, so several transfers can run at once and
a slow sender does not hold up the others. If a file arrives where one of that name
already exists, it is saved as `name-1.ext`, `name-2.ext`, and so on, rather than
overwriting. A failed or malformed transfer is logged and the server keeps running.
Press Ctrl+C to stop it.

The client sends on a background thread, so its window stays responsive during a
large transfer. Per-file progress appears in its console window, overall progress in
the window itself, and the outcome in a dialog.

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
* A single connection only moves files one way, from client to server. Run the
  server on both machines to transfer in either direction.
* Folders are rebuilt from the files inside them, so a completely empty sub-folder
  is not recreated on the other side.
* File permissions and timestamps are not preserved; only names, folder structure
  and contents.

Protocol
--------

The client opens one TCP connection for the whole batch and, for each file, sends a
newline-terminated header:

```
<relative/path><SEPARATOR><filesize>\n
```

followed by exactly `filesize` bytes of content. It repeats that for every file and
then closes the connection, which is how the server knows the batch has ended. One
connection per batch rather than per file means sending a folder of several thousand
files does not open several thousand sockets.

The server reads up to the newline to find the header boundary, then reads exactly
that many bytes. The newline matters: TCP is a byte stream with no message
boundaries, so without a delimiter the header and the start of the file can arrive
in the same packet and be read together.

The relative path carries the folder structure, for example `holiday/day1/img.jpg`.
Because that path arrives over the network, the server treats it as untrusted: it
drops `..` segments, drive letters and leading slashes, and refuses anything that
would still resolve outside `REC`. A sender therefore cannot write to an arbitrary
location on the receiving machine.

Contributing
------------

Contributions are welcome! If you have any suggestions, improvements, or bug fixes, please open an issue or a pull request.

License
-------

This project is licensed under the [MIT License](LICENSE).

Acknowledgements
----------------

This project was inspired by the need for a simple file transfer mechanism using TCP sockets in Python. Special thanks to the developers of PyQt5 and tqdm for their excellent libraries.
