import time
import socket
import json
import random
import select
import struct

class PicoListener:
    
    def __init__(self, HOST='0.0.0.0', PORT=8001):
        self.setup_socket_server(HOST, PORT)
        
        
    def setup_socket_server(self, host, port, max_waiting=5):
        self.listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listening_socket.bind((host, port))
        self.inputs= [self.listening_socket]
        self.outputs=[]
        self.listening_socket.listen(max_waiting)
        
        
    def listen_for_pico(self):
        while len(self.inputs) > 0 or len(self.outputs) > 0:
            readable, writable, exceptions= select.select(self.inputs, self.outputs, self.inputs)
            self.handle_input(readable)
            self.handle_output(writable)
            time.sleep(0.05)
        
    def handle_input(self, readable):
        for s in readable:
            try:
                if s==self.listening_socket:
                    pico_connection, pico_addr= s.accept()
                    self.inputs.append(pico_connection)
                    print("new connection")
                    self.outputs.append(pico_connection)
                else:
                    length_prefix = self.recv_all(s, 4)
                    msg_length = struct.unpack('>I', length_prefix)[0]
                    data= json.loads(self.recv_all(s, msg_length).decode())
                    print(f"recieved data from {s.getpeername()[0]}:{data}")
                    #publish
            except BlockingIOError as e:
                print(f"socket {s.getpeername()} button unavailable. skipping")
            except OSError as e:
                self.shut_socket(s, readable=readable)
                
                
    def handle_output(self, writable):
        for s in writable:
            n=random.random()
            if n<0.3:
                try:
                    encoded_msg= 'LED'.encode()
                    message_length=len(encoded_msg)
                    length_prefix= struct.pack('>I', message_length)
                    s.sendall(length_prefix + encoded_msg)
                except BlockingIOError as e:
                    print(f"socket {s.getpeername()} temp unavailable. skipping")
                except OSError as e:
                    self.shut_socket(s, writable=writable)
                    
                    
    def recv_all(self, sock, length):
        data=b''
        while len(data) < length:
            more=sock.recv(length-len(data))
            if not more:
                print("connection hung up")
                raise OSError("read is too short")
            data+=more
        return data
    
    def shutdown_sockets(self):
        print(f"shutting sockets")
        for s in self.inputs:
            s.close()
        for s in self.outputs:
            s.close()
            
    def shut_socket(self, s, readable=None, writable=None):
        s.close()
        if s in self.inputs:
            self.inputs.remove(s)
        if s in self.outputs:
            self.outputs.remove(s)
        if readable and s in readable:
            readable.remove(s)
        if writable and s in writable:
            writable.remove(s)
def main():
    pico_listener=PicoListener()
    try:
        pico_listener.listen_for_pico()
    except KeyboardInterrupt:
        pass
    finally:
        pico_listener.shutdown_sockets()
        
main()

    
