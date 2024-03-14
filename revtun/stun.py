import socket
import threading
import time
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TunnelManager:
    def __init__(self, tunnel_hostname, tunnel_port, forward_hostname, forward_port, shared_key, buffer_size=20000):
        self.tunnel_hostname = tunnel_hostname
        self.tunnel_port = tunnel_port
        self.forward_hostname = forward_hostname
        self.forward_port = forward_port
        self.shared_key = shared_key
        self.buffer_size = buffer_size
        self.tunnel_conn = None
        self.rppf_conn = None
        self.rppf_conn_lock = threading.Lock()

    def handle_client_authentication(self, client_socket):
        try:
            key = client_socket.recv(1024).decode()
            logger.info(f"Received key from client: {key}")

            if key == self.shared_key:
                logger.info("Client authenticated successfully.")
                return True
            else:
                logger.error("Authentication failed.")
                return False

        except Exception as e:
            logger.error(f"Error handling client authentication: {e}")
            return False

    def make_listening_server(self, address):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(address)
        server_socket.listen()
        return server_socket

    def reset_connections(self):
        with self.rppf_conn_lock:
            try:
                if self.tunnel_conn:
                    self.tunnel_conn.shutdown(socket.SHUT_RDWR)
                    self.tunnel_conn.close()
                if self.rppf_conn:
                    self.rppf_conn.shutdown(socket.SHUT_RDWR)
                    self.rppf_conn.close()

                tunnel_address = (self.tunnel_hostname, self.tunnel_port)
                with self.make_listening_server(tunnel_address) as tunnel_socket:
                    self.tunnel_conn, _ = tunnel_socket.accept()

                rppf_address = (self.forward_hostname, self.forward_port)
                with self.make_listening_server(rppf_address) as rppf_socket:
                    with self.rppf_conn_lock:
                        self.rppf_conn, _ = rppf_socket.accept()

            except Exception as e:
                logger.error(f"Error resetting connections: {e}")
                self.close_connections()

    def tunnel2rppf(self):
        while True:
            try:
                data = self.tunnel_conn.recv(self.buffer_size)
                if not data:
                    logger.info("Tunnel connection interrupted. Closing connections and stopping the program.")
                    self.close_connections()
                    break

                with self.rppf_conn_lock:
                    self.rppf_conn.sendall(data)
                    logger.info(f"Data sent to RPPF: {data}")

            except Exception as e:
                logger.error(f"Error communicating with RPPF: {e}")
                logger.info("Closing connections and stopping the program.")
                self.close_connections()
                break

    def rppf2tunnel(self):
        while True:
            try:
                data = self.rppf_conn.recv(self.buffer_size)
                if not data:
                    logger.info("Connection with RPPF interrupted. Closing connections and stopping the program.")
                    self.close_connections()
                    break

                self.tunnel_conn.sendall(data)
                logger.info(f"Data received from RPPF: {data}")

            except Exception as e:
                logger.error(f"Error communicating with the tunnel: {e}")
                logger.info("Closing connections and stopping the program.")
                self.close_connections()
                break

    def start_tunneling(self):
        try:
            logger.info("Waiting for incoming tunnel connection...")
            tunnel_address = (self.tunnel_hostname, self.tunnel_port)
            with self.make_listening_server(tunnel_address) as tunnel_socket:
                client_socket, _ = tunnel_socket.accept()
                if not self.handle_client_authentication(client_socket):
                    return

                self.tunnel_conn = client_socket
                logger.info("Tunnel established")

            logger.info("Opening RPPF listening service...")
            rppf_address = (self.forward_hostname, self.forward_port)
            with self.make_listening_server(rppf_address) as rppf_socket:
                logger.info(f"RPPF service opened on {str(rppf_address)}")
                logger.info("Ready to transfer data")
                tunnel2rppf_t = threading.Thread(target=self.tunnel2rppf)
                rppf2tunnel_t = threading.Thread(target=self.rppf2tunnel)
                tunnel2rppf_t.daemon = True
                rppf2tunnel_t.daemon = True
                with self.rppf_conn_lock:
                    self.rppf_conn, _ = rppf_socket.accept()

                tunnel2rppf_t.start()
                rppf2tunnel_t.start()

                while True:
                    try:
                        tunnel2rppf_t.join(1)
                        rppf2tunnel_t.join(1)

                        if not tunnel2rppf_t.is_alive() or not rppf2tunnel_t.is_alive():
                            logger.info("One of the threads was interrupted. Attempting to reset...")
                            self.reset_connections()
                            time.sleep(1)

                    except KeyboardInterrupt:
                        self.close_connections()
                        logger.info('\nClosing connections')
                        logger.info('\nShutdown initiated')
                        break

        except Exception as e:
            logger.error('An exception occurred')
            logger.error(e)
            logger.error('Attempting to close sockets')
            self.close_connections()

        while True:
            time.sleep(1)

    def close_connections(self):
        if hasattr(self, 'tunnel_socket'):
            self.tunnel_socket.shutdown(socket.SHUT_RDWR)
            self.tunnel_socket.close()
        if hasattr(self, 'rppf_socket'):
            self.rppf_socket.shutdown(socket.SHUT_RDWR)
            self.rppf_socket.close()
        exit()

def parse_arguments():
    parser = argparse.ArgumentParser(description='Tunneling Manager')
    parser.add_argument('--tunnel', default='16.16.16.114:10000', help='Tunnel address in the format "host:port"')
    parser.add_argument('--forward', default='127.0.0.1:3389', help='Forward address in the format "host:port"')
    parser.add_argument('--shared-key', default='lol', help='Shared key for authentication')

    args = parser.parse_args()

    try:
        tunnel_address_parts = args.tunnel.split(':')
        forward_address_parts = args.forward.split(':')
        tunnel_hostname = tunnel_address_parts[0]
        tunnel_port = int(tunnel_address_parts[1])
        forward_hostname = forward_address_parts[0]
        forward_port = int(forward_address_parts[1])
        shared_key = args.shared_key 
        return tunnel_hostname, tunnel_port, forward_hostname, forward_port, shared_key

    except (ValueError, IndexError):
        parser.error("Invalid address format. Please use the format 'host:port' for both --tunnel and --forward.")

if __name__ == "__main__":
    # Parse command-line arguments
    tunnel_hostname, tunnel_port, forward_hostname, forward_port, shared_key = parse_arguments()

    try:
        tunnel_manager = TunnelManager(
            tunnel_hostname=tunnel_hostname,
            tunnel_port=tunnel_port,
            forward_hostname=forward_hostname,
            forward_port=forward_port,
            shared_key=shared_key
        )
        tunnel_manager.start_tunneling()

    except Exception as e:
        logger.error(e)

