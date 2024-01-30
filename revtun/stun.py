import socket
import threading
import time
import argparse
  

class TunnelManager:
    def __init__(self, tunnel_hostname, tunnel_port, forward_hostname, forward_port, buffer_size=20000):
        self.tunnel_hostname = tunnel_hostname
        self.tunnel_port = tunnel_port
        self.forward_hostname = forward_hostname
        self.forward_port = forward_port
        self.buffer_size = buffer_size
        self.tunnel_conn = None
        self.rppf_conn = None
        self.rppf_conn_lock = threading.Lock()

    def make_listening_server(self, address):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(address)
        server_socket.listen()
        return server_socket
    
    def reset_connections(self):
        with self.rppf_conn_lock:
            try:
                # Close existing connections
                if self.tunnel_conn:
                    self.tunnel_conn.shutdown(socket.SHUT_RDWR)
                    self.tunnel_conn.close()
                if self.rppf_conn:
                    self.rppf_conn.shutdown(socket.SHUT_RDWR)
                    self.rppf_conn.close()

                # Reset connections
                tunnel_address = (self.tunnel_hostname, self.tunnel_port)
                self.tunnel_socket = self.make_listening_server(tunnel_address)
                self.tunnel_conn, _ = self.tunnel_socket.accept()

                rppf_address = (self.forward_hostname, self.forward_port)
                self.rppf_socket = self.make_listening_server(rppf_address)

                with self.rppf_conn_lock:
                    self.rppf_conn, _ = self.rppf_socket.accept()

            except Exception as e:
                print(f"Error resetting connections: {e}")
                self.close_connections()

    def tunnel2rppf(self):
        while True:
            try:
                data = self.tunnel_conn.recv(self.buffer_size)
                if not data:
                    print("Tunnel connection interrupted. Closing connections and stopping the program.")
                    self.close_connections()
                    break

                with self.rppf_conn_lock:
                    self.rppf_conn.sendall(data)
                    print(f"Data sent to RPPF: {data}")

            except Exception as e:
                print(f"Error communicating with RPPF: {e}")
                print("Closing connections and stopping the program.")
                self.close_connections()
                break

    def rppf2tunnel(self):
        while True:
            try:
                data = self.rppf_conn.recv(self.buffer_size)
                if not data:
                    print("Connection with RPPF interrupted. Closing connections and stopping the program.")
                    self.close_connections()
                    break

                self.tunnel_conn.sendall(data)
                print(f"Data received from RPPF: {data}")

            except Exception as e:
                print(f"Error communicating with the tunnel: {e}")
                print("Closing connections and stopping the program.")
                self.close_connections()
                break

    def start_tunneling(self):
        try:
            print("Waiting for incoming tunnel connection...")
            tunnel_address = (self.tunnel_hostname, self.tunnel_port)
            self.tunnel_socket = self.make_listening_server(tunnel_address)
            self.tunnel_conn, _ = self.tunnel_socket.accept()
            print("Tunnel established")

            print("Opening RPPF listening service...")
            rppf_address = (self.forward_hostname, self.forward_port)
            self.rppf_socket = self.make_listening_server(rppf_address)
            print(f"RPPF service opened on {str(rppf_address)}")
            print("Ready to transfer data")

            # Start threads for incoming and outgoing traffic
            tunnel2rppf_t = threading.Thread(target=self.tunnel2rppf)
            rppf2tunnel_t = threading.Thread(target=self.rppf2tunnel)
            tunnel2rppf_t.daemon = True
            rppf2tunnel_t.daemon = True

            # Start threads only after initializing the connection with RPPF
            with self.rppf_conn_lock:
                self.rppf_conn, _ = self.rppf_socket.accept()

            tunnel2rppf_t.start()
            rppf2tunnel_t.start()

            while True:
                try:
                    tunnel2rppf_t.join(1)
                    rppf2tunnel_t.join(1)

                    if not tunnel2rppf_t.is_alive() or not rppf2tunnel_t.is_alive():
                        print("One of the threads was interrupted. Attempting to reset...")
                        self.reset_connections()
                        time.sleep(1)

                except KeyboardInterrupt:
                    self.close_connections()
                    print('\nClosing connections')
                    print('\nShutdown initiated')
                    break

        except Exception as e:
            print('An exception occurred')
            print(e)
            print('Attempting to close sockets')
            self.close_connections()

    def close_connections(self):
        self.tunnel_socket.shutdown(socket.SHUT_RDWR)
        self.tunnel_socket.close()
        self.rppf_socket.shutdown(socket.SHUT_RDWR)
        self.rppf_socket.close()
        exit()

def parse_arguments():
    parser = argparse.ArgumentParser(description="Tunnel Manager for forwarding data between a tunnel and a remote port.")

    # Define command-line arguments
    parser.add_argument('--tunnel-hostname', default='16.16.16.114', help="Hostname for the tunnel (default: 16.16.16.114)")
    parser.add_argument('--tunnel-port', type=int, default=10000, help="Port for the tunnel (default: 10000)")
    parser.add_argument('--forward-hostname', default='16.16.16.114', help="Hostname for forwarding (default: 16.16.16.114)")
    parser.add_argument('--forward-port', type=int, default=3389, help="Port for forwarding (default: 3389)")

    return parser.parse_args()

if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_arguments()

    # Usage with command-line arguments
    try:
        tunnel_manager = TunnelManager(
            tunnel_hostname=args.tunnel_hostname,
            tunnel_port=args.tunnel_port,
            forward_hostname=args.forward_hostname,
            forward_port=args.forward_port
        )
        tunnel_manager.start_tunneling()

    except Exception as e:
        print(e)
