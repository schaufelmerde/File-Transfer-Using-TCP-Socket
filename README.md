TCP Socket File Transfer using Python
=====================================

This repository contains a simple file transfer application using TCP sockets in Python. It consists of a server and a client that allow you to send files from the client to the server, either on the same machine or across a local network.

Prerequisites
-------------

To run this application, you need to have the following installed:

* Python 3.8 - 3.13. PyQt5 has no wheels for Python 3.14 yet, so 3.14 will fail to install the dependencies.
* Either `venv` (bundled with Python) or `pipenv`

Installation
------------

1. Clone the repository to your local machine:

    ```shell
    git clone https://github.com/shitan198u/File-Transfer-Using-TCP-Socket.git
    ```

2. Navigate to the project directory:

    ```shell
    cd File-Transfer-Using-TCP-Socket
    ```

3. Create a virtual environment and install the dependencies:

    ```shell
    python -m venv .venv
    .venv\Scripts\python.exe -m pip install pyqt5 tqdm     # Windows
    ```

    ```shell
    python3 -m venv .venv
    .venv/bin/python -m pip install pyqt5 tqdm             # macOS / Linux
    ```

    If you have a specific Python version installed alongside a newer one, name it
    explicitly — for example `py -3.12 -m venv .venv` on Windows.

4. Activate the virtual environment:

    ```shell
    .venv\Scripts\Activate.ps1     # Windows PowerShell
    source .venv/bin/activate      # macOS / Linux
    ```

<details>
<summary>Alternative: using pipenv</summary>

```shell
pip install pipenv
pipenv install
pipenv shell
```

This uses the `Pipfile`, which pins Python 3.11.

</details>

Usage
-----

The machine that **receives** files runs the server. The machine that **sends** files runs the client. Start the server first.

### Server (the receiving machine)

```shell
python server.py
```

The server listens on `0.0.0.0:5555`, meaning it accepts connections from any network interface, not just the local machine. Received files are saved in the `./REC` directory, which is created if it does not exist.

The server handles each client in its own thread, so several transfers can run at once. If two clients send a file with the same name, the later ones are saved as `name-1.ext`, `name-2.ext`, and so on, rather than overwriting. Press Ctrl+C to stop it.

### Client (the sending machine)

```shell
python client.py
```

The client application will open a graphical user interface (GUI) window:

1. Enter the **Server IP** of the receiving machine (`127.0.0.1` if the server is on this same computer) and the **Port** (`5555` by default).
2. Click **Choose File** and select the file you want to send.
3. The selected file's path will be displayed below the button.
4. Click **Send File**.

Transfer progress is shown in the console as a speed and progress bar. A dialog confirms success, or reports what went wrong if the transfer failed.

Transferring from a PC to a laptop
----------------------------------

Say you want to send files **from your PC to your laptop**. The laptop is receiving, so the laptop runs the server.

**1. On the laptop (receiving), find its IP address:**

```shell
ipconfig                      # Windows — look for "IPv4 Address" under your active adapter
ip addr | grep "inet "        # Linux
ifconfig | grep "inet "       # macOS
```

You want the address of the network you are actually connected to, typically starting `192.168.`, `10.`, or `172.`.

**2. On the laptop, start the server:**

```shell
python server.py
```

**3. On the laptop, allow the port through the firewall.** This is the most common reason transfers fail. On Windows, run this once in an **Administrator** PowerShell:

```powershell
New-NetFirewallRule -DisplayName "TCP File Transfer" -Direction Inbound -LocalPort 5555 -Protocol TCP -Action Allow
```

Windows may instead show a "Windows Defender Firewall has blocked some features" prompt the first time you run the server — allowing it on **Private networks** does the same thing. On Linux with ufw, use `sudo ufw allow 5555/tcp`.

To remove the rule again afterwards:

```powershell
Remove-NetFirewallRule -DisplayName "TCP File Transfer"
```

**4. On the PC (sending), start the client:**

```shell
python client.py
```

Enter the laptop's IP address in the **Server IP** field, choose a file, and click **Send File**. The file appears in the `REC` folder on the laptop.

To send the other way, from laptop to PC, simply swap the roles: run `server.py` on the PC and `client.py` on the laptop.

### Troubleshooting

| Symptom | Likely cause |
| --- | --- |
| Dialog says the connection timed out | Firewall on the receiving machine is blocking port 5555 (see step 3), or the two machines are not on the same network |
| Dialog says the connection was actively refused | The server isn't running on the receiving machine, or you typed the wrong port |
| Wrong machine receives nothing | IP address typo, or you took the IP of the wrong adapter — check `ipconfig` again |
| `ModuleNotFoundError: No module named 'PyQt5'` | The virtual environment isn't activated, or you installed into a different Python |
| Both machines on Wi-Fi but cannot connect | Some networks (guest Wi-Fi, public hotspots) isolate clients from each other. Try a different network or a wired connection |

Notes and limitations
---------------------

* **Transfers are not encrypted or authenticated.** Anything sent travels over the network in plain text, and the server accepts a file from anyone who can reach the port. Use this on networks you trust, and stop the server when you are done with it.
* Both machines must be on the same local network. This is not designed to work across the internet.
* The transfer is one-way: clients send, the server receives.

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
