import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QComboBox, QMessageBox
from pyrad.client import Client
from pyrad.packet import AccessRequest, AccessAccept, AccessReject

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
        self.secret_label = QLabel("Shared Secret:")
        self.secret_input = QLineEdit()
        self.secret_input.setEchoMode(QLineEdit.Password)

        # Username
        self.username_label = QLabel("Username:")
        self.username_input = QLineEdit()

        # Password
        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        # Test Button
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self.test_radius_connection)

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
        layout.addWidget(self.test_button)

        # Central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def test_radius_connection(self):
        server = self.server_input.text()
        port = int(self.port_input.text())
        secret = self.secret_input.text().encode('utf-8')
        username = self.username_input.text()
        password = self.password_input.text()

        try:
            client = Client(server=server, secret=secret)
            client.auth_port = port

            # Create RADIUS authentication request
            req = client.CreateAuthPacket(code=AccessRequest, User_Name=username)
            req["User-Password"] = req.PwCrypt(password)

            # Send request and get reply
            reply = client.SendPacket(req)

            # Check the response from the server
            if reply.code == AccessAccept:
                QMessageBox.information(self, "Success", "Access-Accept received: Connection Successful")
            elif reply.code == AccessReject:
                QMessageBox.warning(self, "Failed", "Access-Reject received: Invalid credentials")
            else:
                QMessageBox.critical(self, "Error", "No response from server or unknown error")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RadiusTester()
    window.show()
    sys.exit(app.exec_())