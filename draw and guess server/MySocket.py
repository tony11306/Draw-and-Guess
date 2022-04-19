import pickle
import socket
import struct

class SocketData:
    def __init__(self, data_type, x=None, y=None, thickness=None, color=None, user_list=None, message=None, user_name=None, user_id=None, question=None, time=None) -> None:
        self.data_type = data_type
        self.x = x
        self.y = y
        self.thickness = thickness
        self.color = color
        self.user_list = user_list
        self.message = message
        self.user_name = user_name
        self.user_id = user_id
        self.question = question
        self.time = time
    
    def __str__(self) -> str:
        def wrap(s):
            return 'SocketData(' + s + ')'
        if self.data_type == 'draw':
            return wrap(f'data_type=draw, x={self.x}, y={self.y}, thickness={self.thickness}, color={self.color}')
        elif self.data_type == 'user_list':
            return wrap(f'data_type=user_list, user_list={self.user_list}')
        elif self.data_type == 'message':
            return wrap(f'data_type=message, message={self.message}')
        elif self.data_type == 'ready':
            return wrap(f'data_type=ready')
        elif self.data_type == 'register_request':
            return wrap(f'data_type=register_request, user_name={self.user_name}')
        elif self.data_type == 'register_response':
            return wrap(f'data_type=register_response, user_id={self.user_id}')
        elif self.data_type == 'selecting_question':
            return wrap(f'data_type=selecting_options, question={self.question}')
        
        return wrap(f'data_type={self.data_type}')

class MySocket(socket.socket):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._socket = super()
    
    def accept(self):
        conn, addr = super().accept()
        sokt = MySocket(socket.AF_INET, socket.SOCK_STREAM)
        sokt.set_socket(conn)
        return sokt, addr
    
    def bind(self, address):
        self._socket.bind(address)

    def listen(self, backlog):
        self._socket.listen(backlog)
    
    def close(self):
        self._socket.close()
    
    def set_socket(self, socket):
        self._socket = socket

    def sendall(self, data: SocketData):
        data = pickle.dumps(data)
        data = struct.pack('!I', len(data)) + data
        self._socket.send(data)

    def _recv_all(self, length):
        data = b''
        while len(data) < length:
            packet = self._socket.recv(length - len(data))
            if not packet:
                return None
            data += packet
        return data

    def recv(self) -> SocketData:
        data_length = self._recv_all(4)
        if not data_length:
            return None
        
        data_length = struct.unpack('!I', data_length)[0]
        data = self._recv_all(data_length)
        if not data:
            return None
        return pickle.loads(data)