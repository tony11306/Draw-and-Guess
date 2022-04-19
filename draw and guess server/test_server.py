import socket
import pickle
import threading
import struct
from GameModel import GameModel
from MySocket import MySocket, SocketData
import json

# create a socket at localhost:1234 that recv data and print it
if __name__ == '__main__':

    # open a json file
    ip = ''
    port = 1234
    with open('server_settings.json', 'r') as f:
        server_settings = json.load(f)
        GameModel.minimum_players_to_start = server_settings['minimum-players-to-start']
        GameModel.selecting_options_time = server_settings['selecting-options-time']
        GameModel.drawing_time = server_settings['drawing-time']
        GameModel.show_answer_time = server_settings['show-answer-time']
        GameModel.winning_score = server_settings['winning-score']
        GameModel.show_finished_time = server_settings['show-finished-time']
        ip = server_settings['server-ip']
        port = server_settings['server-port']



    game_model = GameModel()
    thread = threading.Thread(target=game_model.run)
    thread.daemon = True
    thread.start()
    s = MySocket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((ip, port))
    s.listen(10)
    print('Server is now running...')
    while True:
        conn, addr = s.accept()
        print('connected by', addr)
        if not game_model.register_client(addr, conn):
            conn.close()



