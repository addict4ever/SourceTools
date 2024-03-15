import socket
import threading
import time
import argparse
import logging
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TunnelingServer:
    def __init__(self, tunnel_address, forward_address, rsa_key_path, shared_key):
        self.tunnel_address = tunnel_address
        self.forward_address = forward_address
        self.rsa_key_path = rsa_key_path
        self.shared_key = shared_key  # Initialize shared key here
        self.tunnel_socket = None
        self.forward_socket = None
        self.sending_socket_lock = threading.Lock()
        self.receiving_socket_lock = threading.Lock()
        self.last_data_received_time = time.time()

    def establish_connection(self, address):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server_socket.bind(address)
            server_socket.listen(1)
            logger.info(f"Server listening on {address}")
            client_socket, _ = server_socket.accept()
            logger.info(f"Connection established with client {client_socket.getpeername()}")
        except socket.error as e:
            logger.error(f"Error binding server socket to {address}: {e}")
            raise

        return client_socket

    def close_and_exit(self):
        self.close_connections()
        logger.info('\nStopped correctly')
        exit(1)

    def tunnel2forward(self):
        try:
            while True:
                data = self.tunnel_socket.recv(20000)
                if not data:
                    current_time = time.time()
                    elapsed_time = current_time - self.last_data_received_time
                    if elapsed_time > 60:
                        logger.info("No data received for a long time. Reconnecting...")
                        continue

                    raise Exception("Tunnel has dropped, this shouldn't happen, restart RPPF.")

                self.last_data_received_time = time.time()

                self.sending_socket_lock.acquire()
                self.forward_socket.sendall(data)
                self.sending_socket_lock.release()

        except Exception as e:
            logger.error(f"Exception in tunnel2forward: {e}")
            self.close_and_exit()

    def forward2tunnel(self):
        while True:
            try:
                self.receiving_socket_lock.acquire()
                data = self.forward_socket.recv(20000)
                self.receiving_socket_lock.release()

                if not data:
                    continue

                self.tunnel_socket.sendall(data)

            except (ConnectionResetError, OSError):
                logger.error("Connection reset by peer or OSError in forward2tunnel. Reconnecting...")

            except Exception as e:
                logger.error(f"Exception in forward2tunnel: {e}")

    def stop_threads(self):
        if hasattr(self, 'tunnel2forward_t') and self.tunnel2forward_t.is_alive():
            self.tunnel2forward_t.join()
        if hasattr(self, 'forward2tunnel_t') and self.forward2tunnel_t.is_alive():
            self.forward2tunnel_t.join()

    def start_tunneling(self):
        try:
            logger.info("Creating tunnel to " + str(self.tunnel_address))
            self.tunnel_socket = self.establish_connection(self.tunnel_address)
            logger.info("Tunnel created")
            logger.info("Encrypting and sending shared key")
            self.encrypt_shared_key()
            logger.info("Opening forward connection to " + str(self.forward_address))
            self.forward_socket = self.establish_connection(self.forward_address)
            logger.info("Connection created")
            logger.info("--------------------------------------------")
            logger.info("Ready to transfer data")
            self.tunnel2forward_t = threading.Thread(target=self.tunnel2forward)
            self.forward2tunnel_t = threading.Thread(target=self.forward2tunnel)
            self.tunnel2forward_t.daemon = True
            self.forward2tunnel_t.daemon = True
            self.tunnel2forward_t.start()
            self.forward2tunnel_t.start()
            self.tunnel2forward_t.join()
            self.forward2tunnel_t.join()

        except KeyboardInterrupt:
            self.stop_threads()
            self.close_connections()
            logger.info('\nStopped correctly')
            exit(0)

        except Exception as e:
            logger.error('An exception occurred')
            logger.error(e)
            logger.error('Trying to close sockets')
            self.stop_threads()
            self.close_connections()
            logger.info('\nStopped correctly')
            exit(1)
    
    def close_connections(self):

        if self.tunnel_socket:
            self.tunnel_socket.shutdown(socket.SHUT_RDWR)
            self.tunnel_socket.close()
        if self.forward_socket:
            self.forward_socket.shutdown(socket.SHUT_RDWR)
            self.forward_socket.close()

    def encrypt_shared_key(self):
        try:
            if not self.shared_key:
                raise ValueError("Shared key not set")

            with open(self.rsa_key_path, 'r') as f:
                rsa_key = RSA.import_key(f.read())

            cipher_rsa = PKCS1_OAEP.new(rsa_key)
            encrypted_key = cipher_rsa.encrypt(self.shared_key.encode())

            logger.info(f"Encrypted shared key: {encrypted_key}")
            self.tunnel_socket.sendall(encrypted_key)

        except Exception as e:
            logger.error(f"Error encrypting shared key: {e}")
            self.close_and_exit()

def parse_arguments():
    parser = argparse.ArgumentParser(description='Tunneling Server')
    parser.add_argument('--tunnel', default='16.16.16.114:10000', help='Tunnel address in the format "host:port"')
    parser.add_argument('--forward', default='127.0.0.1:3389', help='Forward address in the format "host:port"')
    parser.add_argument('--rsa-key', default='test_rsa.key', help='Path to server RSA key')
    parser.add_argument('--shared-key', required=True, help='Shared key for authentication')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_arguments()

    tunnel_host, tunnel_port = args.tunnel.split(':')
    forward_host, forward_port = args.forward.split(':')
    tunnel_address = (tunnel_host, int(tunnel_port))
    forward_address = (forward_host, int(forward_port))
    tunneling_server = TunnelingServer(
        tunnel_address=tunnel_address,
        forward_address=forward_address,
        rsa_key_path=args.rsa_key,
        shared_key=args.shared_key
    )
    tunneling_server.start_tunneling()
