import sys
import socket
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QMessageBox
from pyrad.client import Client
from pyrad.packet import AccessRequest, AccessAccept, AccessReject
import select

class RadiusTester(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RADIUS Server Tester")

        # Server Address
        self.server_label = QLabel("Server Address:")
        self.server_input = QLineEdit()

        # Port
        self.port_label = QLabel("Port:")
        self.port_input = QLineEdit("1812")

        # Shared Secret
        self.secret_label = QLabel("Shared Secret (for RADIUS):")
        self.secret_input = QLineEdit()
        self.secret_input.setEchoMode(QLineEdit.Password)

        # Username (for RADIUS authentication)
        self.username_label = QLabel("Username (for RADIUS):")
        self.username_input = QLineEdit()

        # Password (for RADIUS authentication)
        self.password_label = QLabel("Password (for RADIUS):")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        # Test Buttons
        self.test_port_button = QPushButton("Test if Port is Open")
        self.test_port_button.clicked.connect(self.test_port)

        self.ping_button = QPushButton("Ping Server")
        self.ping_button.clicked.connect(self.ping_server)

        self.radius_test_button = QPushButton("Test RADIUS Authentication")
        self.radius_test_button.clicked.connect(self.test_radius_connection)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.server_label)
        layout.addWidget(self.server_input)
        layout.addWidget(self.port_label)
        layout.addWidget(self.port_input)
        layout.addWidget(self.secret_label)
        layout.addWidget(self.secret_input)
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.test_port_button)
        layout.addWidget(self.ping_button)
        layout.addWidget(self.radius_test_button)

        # Central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def test_port(self):
        server = self.server_input.text()
        port = int(self.port_input.text())

        try:
            # Essayez de vous connecter au port via un socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)  # Timeout de 5 secondes
                result = sock.connect_ex((server, port))
                if result == 0:
                    QMessageBox.information(self, "Success", f"Port {port} is open on {server}")
                else:
                    QMessageBox.warning(self, "Failed", f"Port {port} is not open on {server}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def ping_server(self):
        server = self.server_input.text()
        # Commande ping (Sur Windows, utiliser 'ping -n 1')
        response = os.system(f"ping -c 1 {server}")
        if response == 0:
            QMessageBox.information(self, "Success", f"{server} is reachable.")
        else:
            QMessageBox.warning(self, "Failed", f"{server} is not reachable.")

    def test_radius_connection(self):
        server = self.server_input.text()
        port = int(self.port_input.text())
        secret = self.secret_input.text().encode('utf-8')
        username = self.username_input.text()
        password = self.password_input.text()

        try:
            client = Client(server=server, secret=secret)
            client.auth_port = port

            # Créer une requête d'authentification RADIUS
            req = client.CreateAuthPacket(code=AccessRequest, User_Name=username)
            req["User-Password"] = req.PwCrypt(password)

            # Utiliser select.select() pour attendre la réponse avec un timeout de 5 secondes
            client.SendPacket(req)
            ready_sockets, _, _ = select.select([client.socket], [], [], 5.0)

            if ready_sockets:
                # Recevoir la réponse
                reply = client.RecvPacket()
                if reply.code == AccessAccept:
                    QMessageBox.information(self, "Success", "Access-Accept received: Connection Successful")
                elif reply.code == AccessReject:
                    QMessageBox.warning(self, "Failed", "Access-Reject received: Invalid credentials")
                else:
                    QMessageBox.critical(self, "Error", "Unknown response code from server")
            else:
                QMessageBox.critical(self, "Error", "Timeout: No response from server")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RadiusTester()
    window.show()
    sys.exit(app.exec_())