import socket
import time
import sys
import threading
import datetime

reset_counter = 0
MAX_RESET_COUNT = 10
BUFFER_SIZE = 20000

class TunnelingClient:
    def __init__(self, tunnel_address, forward_address):
        self.tunnel_address = tunnel_address
        self.forward_address = forward_address
        self.tunnel_socket = None
        self.forward_socket = None
        self.sending_socket_lock = threading.Lock()
        self.receiving_socket_lock = threading.Lock()
        self.last_data_received_time = datetime.datetime.now()

    def establish_connection(self, address):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        while True:
            try:
                client_socket.connect(address)
                break
            except:
                time.sleep(1)

        return client_socket

    def close_and_exit(self):
        # close sockets and exit the program
        self.close_connections()
        print('\nStopped correctly')
        sys.exit(1)

    def tunnel2forward(self):
        try:
            while True:
                data = self.tunnel_socket.recv(BUFFER_SIZE)
                if not data:
                    current_time = datetime.datetime.now()
                    elapsed_time = (current_time - self.last_data_received_time).total_seconds()
                    if elapsed_time > 60:
                        print("No data received for a long time. Reconnecting...")
                        continue

                    raise Exception("Tunnel has dropped, this shouldn't happen, restart RPPF.")

                self.last_data_received_time = datetime.datetime.now()

                self.sending_socket_lock.acquire()
                self.forward_socket.sendall(data)
                self.sending_socket_lock.release()

        except Exception as e:
            print(f"Exception in tunnel2forward: {e}")
            self.close_and_exit()

    def forward2tunnel(self):
        while True:
            try:
                self.receiving_socket_lock.acquire()
                data = self.forward_socket.recv(BUFFER_SIZE)
                self.receiving_socket_lock.release()

                if not data:
                    continue

                self.tunnel_socket.sendall(data)

            except (ConnectionResetError, OSError):
                print("Connection reset by peer or OSError in forward2tunnel. Reconnecting...")

            except Exception as e:
                print(f"Exception in forward2tunnel: {e}")

    def stop_threads(self):
        if hasattr(self, 'tunnel2forward_t') and self.tunnel2forward_t.is_alive():
            self.tunnel2forward_t.join()
        if hasattr(self, 'forward2tunnel_t') and self.forward2tunnel_t.is_alive():
            self.forward2tunnel_t.join()

    def start_tunneling(self):
        try:
            print("Creating tunnel to " + str(self.tunnel_address))
            self.tunnel_socket = self.establish_connection(self.tunnel_address)
            print("Tunnel created")

            print("Opening forward connection to " + str(self.forward_address))
            self.forward_socket = self.establish_connection(self.forward_address)
            print("Connection created")
            print("--------------------------------------------")
            print("Ready to transfer data")

            # start thread for incoming and outgoing traffic
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
            print('\nStopped correctly')
            sys.exit(0)

        except Exception as e:
            print('An exception occurred')
            print(e)
            print('Trying to close sockets')
            self.stop_threads()
            self.close_connections()
            print('\nStopped correctly')
            sys.exit(0)
    
    def close_connections(self):
        # close sockets
        if self.tunnel_socket:
            self.tunnel_socket.shutdown(socket.SHUT_RDWR)
            self.tunnel_socket.close()
        if self.forward_socket:
            self.forward_socket.shutdown(socket.SHUT_RDWR)
            self.forward_socket.close()

tunnel_address = ('16.16.16.114', 10000)
forward_address = ('127.0.0.1', 3389)

tunneling_client = TunnelingClient(tunnel_address, forward_address)
tunneling_client.start_tunneling()
