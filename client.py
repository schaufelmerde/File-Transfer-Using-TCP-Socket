import os
import socket
import tqdm
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 5555
BUFFER_SIZE = 4096
SEPARATOR = "<SEPARATOR>"

class Client(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # the server may be on another machine, so let the user say where
        self.host_input = QtWidgets.QLineEdit(DEFAULT_HOST, self)
        self.port_input = QtWidgets.QLineEdit(str(DEFAULT_PORT), self)

        self.choose_file_button = QtWidgets.QPushButton('Choose File', self)
        self.choose_file_button.clicked.connect(self.choose_file)

        self.file_name_label = QtWidgets.QLabel(self)

        self.send_file_button = QtWidgets.QPushButton('Send File', self)
        self.send_file_button.clicked.connect(self.send_file)

        form = QtWidgets.QFormLayout()
        form.addRow('Server IP:', self.host_input)
        form.addRow('Port:', self.port_input)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(form)
        vbox.addWidget(self.choose_file_button)
        vbox.addWidget(self.file_name_label)
        vbox.addWidget(self.send_file_button)

        self.setLayout(vbox)
        self.setWindowTitle('Client')
        self.show()

    def send_file(self):
        host = self.host_input.text().strip() or DEFAULT_HOST
        port_text = self.port_input.text().strip()

        # get the file name and size
        file_path = self.file_name_label.text()
        if not file_path:
            QMessageBox.warning(self, 'No file', 'Choose a file to send first.')
            return
        try:
            port = int(port_text)
        except ValueError:
            QMessageBox.warning(self, 'Bad port', f'"{port_text}" is not a port number.')
            return

        file_name_only = os.path.basename(file_path)
        filesize = os.path.getsize(file_path)

        # create the client socket, connect to the server
        s = socket.socket()
        try:
            s.connect((host, port))

            # send the filename and filesize, newline-terminated so the server
            # can tell where the header ends and the file contents begin
            s.sendall(f"{file_name_only}{SEPARATOR}{filesize}\n".encode())

            # start sending the file
            progress = tqdm.tqdm(range(filesize), f"Sending {file_name_only}", unit="B", unit_scale=True, unit_divisor=1024)
            with open(file_path, "rb") as f:
                while True:
                    # read the bytes from the file
                    bytes_read = f.read(BUFFER_SIZE)
                    if not bytes_read:
                        # file transmitting is done
                        break
                    # we use sendall to assure transmission in
                    # busy networks
                    s.sendall(bytes_read)
                    # update the progress bar
                    progress.update(len(bytes_read))
        except OSError as e:
            # wrong IP, server not started, or a firewall in the way -- say so
            # in the window rather than only as a console traceback
            QMessageBox.critical(self, 'Transfer failed',
                                 f'Could not send to {host}:{port}\n\n{e}')
            return
        finally:
            # close the socket
            s.close()

        QMessageBox.information(self, 'Sent', f'{file_name_only} sent to {host}:{port}.')

    def choose_file(self):
        file_dialog = QFileDialog()
        file_path = file_dialog.getOpenFileName()[0]
        self.file_name_label.setText(file_path)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    ex = Client()
    app.exec_()
