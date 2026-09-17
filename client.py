import os
import socket
import tqdm
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 5555
BUFFER_SIZE = 4096
SEPARATOR = "<SEPARATOR>"


def collect_files(paths):
    """Expand files and folders into (absolute path, path to send) pairs.

    A folder keeps its own name at the top, so sending C:/pics/holiday
    arrives as holiday/... on the other side, sub-folders and all.
    """
    items = []
    seen = set()
    for path in paths:
        path = os.path.normpath(path)
        if os.path.isdir(path):
            root = os.path.basename(path.rstrip("\\/")) or "folder"
            for dirpath, _dirnames, filenames in os.walk(path):
                for name in sorted(filenames):
                    full = os.path.join(dirpath, name)
                    rel = os.path.relpath(full, path).replace("\\", "/")
                    if full not in seen:
                        seen.add(full)
                        items.append((full, f"{root}/{rel}"))
        elif os.path.isfile(path):
            if path not in seen:
                seen.add(path)
                items.append((path, os.path.basename(path)))
    return items


class SendWorker(QtCore.QThread):
    """Does the transfer off the GUI thread, so the window stays responsive."""

    progress = QtCore.pyqtSignal(int, int, str)
    done = QtCore.pyqtSignal(int, int)
    failed = QtCore.pyqtSignal(str)

    def __init__(self, host, port, items):
        super().__init__()
        self.host = host
        self.port = port
        self.items = items

    def run(self):
        sent = 0
        total_bytes = 0
        s = socket.socket()
        try:
            s.connect((self.host, self.port))
            # the whole batch goes down one connection, so a folder of
            # thousands of files doesn't open thousands of sockets
            for index, (full, relpath) in enumerate(self.items, 1):
                filesize = os.path.getsize(full)
                self.progress.emit(index, len(self.items), relpath)
                s.sendall(f"{relpath}{SEPARATOR}{filesize}\n".encode())
                progress = tqdm.tqdm(range(filesize), f"Sending {relpath}",
                                     unit="B", unit_scale=True, unit_divisor=1024,
                                     leave=False)
                with open(full, "rb") as f:
                    while True:
                        bytes_read = f.read(BUFFER_SIZE)
                        if not bytes_read:
                            break
                        # sendall assures transmission on busy networks
                        s.sendall(bytes_read)
                        progress.update(len(bytes_read))
                progress.close()
                sent += 1
                total_bytes += filesize
        except OSError as e:
            self.failed.emit(f"{e}\n\n{sent} of {len(self.items)} file(s) were sent.")
            return
        finally:
            s.close()
        self.done.emit(sent, total_bytes)


class Client(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.initUI()

    def initUI(self):
        # the server may be on another machine, so let the user say where
        self.host_input = QtWidgets.QLineEdit(DEFAULT_HOST, self)
        self.port_input = QtWidgets.QLineEdit(str(DEFAULT_PORT), self)

        form = QtWidgets.QFormLayout()
        form.addRow('Server IP:', self.host_input)
        form.addRow('Port:', self.port_input)

        self.queue = QtWidgets.QListWidget(self)
        self.queue.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.add_files_button = QtWidgets.QPushButton('Add Files...', self)
        self.add_files_button.clicked.connect(self.add_files)
        self.add_folder_button = QtWidgets.QPushButton('Add Folder...', self)
        self.add_folder_button.clicked.connect(self.add_folder)
        self.remove_button = QtWidgets.QPushButton('Remove Selected', self)
        self.remove_button.clicked.connect(self.remove_selected)
        self.clear_button = QtWidgets.QPushButton('Clear', self)
        self.clear_button.clicked.connect(self.queue.clear)

        buttons = QtWidgets.QHBoxLayout()
        for b in (self.add_files_button, self.add_folder_button,
                  self.remove_button, self.clear_button):
            buttons.addWidget(b)

        self.send_button = QtWidgets.QPushButton('Send', self)
        self.send_button.clicked.connect(self.send)

        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.status_label = QtWidgets.QLabel(
            'Add files or folders, then press Send.', self)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(form)
        vbox.addWidget(QtWidgets.QLabel('Files and folders to send:', self))
        vbox.addWidget(self.queue)
        vbox.addLayout(buttons)
        vbox.addWidget(self.send_button)
        vbox.addWidget(self.progress_bar)
        vbox.addWidget(self.status_label)

        self.setLayout(vbox)
        self.setWindowTitle('Client')
        self.resize(560, 400)
        self.show()

    def queued_paths(self):
        return [self.queue.item(i).text() for i in range(self.queue.count())]

    def add_paths(self, paths):
        existing = set(self.queued_paths())
        for path in paths:
            path = os.path.normpath(path)
            if path and path not in existing:
                existing.add(path)
                self.queue.addItem(path)

    def add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, 'Choose files')
        self.add_paths(paths)

    def add_folder(self):
        # the native dialog only picks one folder at a time, so press this
        # again for each folder you want to add
        path = QFileDialog.getExistingDirectory(self, 'Choose a folder')
        if path:
            self.add_paths([path])

    def remove_selected(self):
        for item in self.queue.selectedItems():
            self.queue.takeItem(self.queue.row(item))

    def set_busy(self, busy):
        for b in (self.send_button, self.add_files_button, self.add_folder_button,
                  self.remove_button, self.clear_button):
            b.setEnabled(not busy)
        self.progress_bar.setVisible(busy)

    def send(self):
        host = self.host_input.text().strip() or DEFAULT_HOST
        port_text = self.port_input.text().strip()
        try:
            port = int(port_text)
        except ValueError:
            QMessageBox.warning(self, 'Bad port', f'"{port_text}" is not a port number.')
            return

        paths = self.queued_paths()
        if not paths:
            QMessageBox.warning(self, 'Nothing to send',
                                'Add some files or folders first.')
            return

        items = collect_files(paths)
        if not items:
            QMessageBox.warning(self, 'Nothing to send',
                                'Those folders contain no files.')
            return

        self.set_busy(True)
        self.progress_bar.setRange(0, len(items))
        self.progress_bar.setValue(0)

        self.worker = SendWorker(host, port, items)
        self.worker.progress.connect(self.on_progress)
        self.worker.done.connect(self.on_done)
        self.worker.failed.connect(self.on_failed)
        self.worker.start()

    def on_progress(self, index, total, name):
        self.progress_bar.setValue(index)
        self.status_label.setText(f'Sending {index} of {total}: {name}')

    def on_done(self, count, total_bytes):
        self.set_busy(False)
        self.status_label.setText(f'Sent {count} file(s), {total_bytes} bytes.')
        QMessageBox.information(self, 'Sent',
                                f'Sent {count} file(s), {total_bytes} bytes.')

    def on_failed(self, message):
        self.set_busy(False)
        self.status_label.setText('Transfer failed.')
        # wrong IP, server not started, or a firewall in the way -- say so
        # in the window rather than only as a console traceback
        QMessageBox.critical(self, 'Transfer failed', message)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    ex = Client()
    app.exec_()
