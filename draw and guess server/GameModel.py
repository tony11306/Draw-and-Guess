import threading
import socket
import pickle
from MySocket import MySocket, SocketData
import time
import random

questions = []

with open('questions.txt', 'r', encoding='utf-8') as f:
    for line in f:
        questions.append(line.strip())

class Player:
    def __init__(self, addr, conn, name, user_id):
        self._addr = addr
        self._conn = conn
        self._name = name
        self._score = 0
        self.score_lock = threading.Lock()
        self._is_correct = False
        self.is_correct_lock = threading.Lock()
        self._user_id = user_id
    
    @property
    def user_id(self):
        return self._user_id

    @property
    def name(self):
        return self._name
    
    @property
    def conn(self):
        return self._conn
    
    @property
    def addr(self):
        return self._addr
    
    @property
    def score(self):
        with self.score_lock:
            return self._score
    
    @score.setter
    def score(self, value):
        with self.score_lock:
            self._score = value
    
    @property
    def is_correct(self):
        return self._is_correct

    @is_correct.setter
    def is_correct(self, value):
        with self.is_correct_lock:
            self._is_correct = value
    


class GameModel:

    minimum_players_to_start = 2
    drawing_time = 45
    show_answer_time = 5
    selecting_options_time = 10
    winning_score = 120
    show_finished_time = 30


    def __init__(self):
        self.players = {} # dict of (addr, client: MySocket)
        self.players_lock = threading.Lock()
        self.id_generator_lock = threading.Lock()
        self.questions = []
        self.draw_history = []
        self.state = 'waiting_to_start' # waiting, selecting_options, drawing, waiting_to_start, answer
        self.state_lock = threading.Lock()
        self.current_turn_player = None
        self.current_index = 0
        self.current_question = None
        self.timer = 0
        self.timer_lock = threading.Lock()
        self.ids = 0

        self.score_plus = 9

    def set_timer(self, time):
        with self.timer_lock:
            if time < 0:
                self.timer = 0
            else:
                self.timer = time

    def run(self):
        while True:
            try:
                time.sleep(0.5)
                self.set_timer(self.timer - 0.5)
                with self.state_lock:
                    if self.state == 'waiting_to_start':
                        self.draw_history = []
                        if len(self.players) >= GameModel.minimum_players_to_start:
                            self.questions = questions.copy()
                            random.shuffle(self.questions)
                            self.state = 'selecting_options'
                            self.update_current_player()
                            data = SocketData(
                                data_type='selecting_options', 
                                question=self.current_question,
                                user_id=self.current_turn_player.user_id,
                                user_name=self.current_turn_player.name
                            )
                            self.broadcast(SocketData(data_type='user_list', user_list=self.get_user_list()))
                            self.set_timer(GameModel.selecting_options_time)
                            self.broadcast(SocketData(data_type='set_time', time=self.timer))
                            self.broadcast(data)
                    elif self.state == 'selecting_options':
                        self.draw_history = []
                        if len(self.players) < GameModel.minimum_players_to_start:
                            self.state = 'waiting_to_start'
                            self.set_timer(0)
                            self.broadcast(SocketData(data_type='waiting_to_start'))
                            self.broadcast(SocketData(data_type='set_time', time=self.timer))
                        else:
                            if self.timer == 0:
                                self.update_current_player()
                                data = SocketData(
                                    data_type='selecting_options', 
                                    question=self.current_question,
                                    user_id=self.current_turn_player.user_id,
                                    user_name=self.current_turn_player.name
                                )
                                self.broadcast(data)
                                self.set_timer(GameModel.selecting_options_time)
                                self.score_plus = 9
                                self.broadcast(SocketData(data_type='set_time', time=self.timer))
                        
                    elif self.state == 'drawing':
                        if len(self.players) < GameModel.minimum_players_to_start:
                            self.state = 'waiting_to_start'
                            self.set_timer(0)
                            self.broadcast(SocketData(data_type='waiting_to_start'))
                            self.broadcast(SocketData(data_type='set_time', time=self.timer))
                        else:
                            is_all_correct = True
                            for player in self.players.values():
                                if player != self.current_turn_player:
                                    is_all_correct = is_all_correct and player.is_correct
                            if is_all_correct or self.timer == 0:
                                data = SocketData(data_type='answer', question=self.current_question)
                                self.broadcast(data)
                                self.state = 'waiting'
                                self.set_timer(GameModel.show_answer_time)
                                self.broadcast(SocketData(data_type='set_time', time=self.timer))
                    elif self.state == 'waiting':
                        if len(self.players) < GameModel.minimum_players_to_start:
                            self.state = 'waiting_to_start'
                            self.set_timer(0)
                            self.broadcast(SocketData(data_type='waiting_to_start'))
                            self.broadcast(SocketData(data_type='set_time', time=self.timer))
                        else:
                            if self.timer > 0:
                                continue
                            is_finished = False
                            for player in self.players.values():
                                player.is_correct = False
                                is_finished = is_finished or player.score >= GameModel.winning_score
                            if is_finished:
                                self.state = 'finished'
                                self.set_timer(GameModel.show_finished_time)
                                self.broadcast(SocketData(data_type='set_time', time=self.timer))
                                self.broadcast(SocketData(data_type='finished'))
                            else:
                                self.state = 'selecting_options'
                    elif self.state == 'finished':
                        self.draw_history = []
                        if len(self.players) == 0:
                            self.state = 'waiting_to_start'
                            continue
                        if self.timer > 0:
                            continue
                        self.state = 'waiting_to_start'
                        for player in self.players.values():
                            player.score = 0
                            
            except Exception as e:
                print('err: ',e)
                pass

    def update_current_player(self):
        with self.players_lock:
            if len(self.players) == 0:
                return
            if len(self.questions) == 0:
                self.questions = questions.copy()
                random.shuffle(self.questions)
            self.current_question = self.questions.pop()
            players = []

            for player in self.players.values():
                players.append(player)

            self.current_turn_player = players[self.current_index % len(players)]
            self.current_index += 1

    def get_user_list(self):
        with self.players_lock:
            return [(player.name, player.score) for player in self.players.values()]

    def submit_data(self, addr, data: SocketData):
        with self.state_lock:
            if data.data_type == 'ready':
                self.broadcast(SocketData(
                        data_type='user_list',
                        user_list=self.get_user_list()
                    )
                )
                self.players[addr].conn.sendall(self.get_current_turn_packet(addr))
                self.players[addr].conn.sendall(SocketData(data_type='set_time', time=self.timer))
                join_message = SocketData(data_type='message', message=f'{self.players[addr].name} 加入了遊戲.')
                self.broadcast(join_message)
                for draw_history in self.draw_history:
                    self.players[addr].conn.sendall(draw_history)
            elif data.data_type == 'message':
                if self.state == 'drawing':
                    if self.players[addr] == self.current_turn_player:
                        return
                    if self.players[addr].is_correct:
                        return
                    if data.message == self.current_question:
                        self.players[addr].is_correct = True
                        self.players[addr].score += self.score_plus
                        self.current_turn_player.score += 10 if self.score_plus == 9 else 2
                        if self.score_plus > 2:
                            self.score_plus -= 1
                        data.message = f'正確答案為: {self.current_question}'
                        self.players[addr].conn.sendall(data)
                        self.broadcast(SocketData(data_type='user_list', user_list=self.get_user_list()))
                        self.broadcast(SocketData(data_type='message', message=f'{self.players[addr].name} 答對了.'))
                        return
                data.message = f'[{self.players[addr].name}]: {data.message}'
                self.broadcast(data)
            elif data.data_type == 'draw' or data.data_type == 'start_draw':
                if self.state != 'drawing':
                    return
                if self.current_turn_player and self.current_turn_player.addr != addr:
                    return
                self.draw_history.append(data)
                self.broadcast(data)
            elif data.data_type == 'skip':
                if self.state == 'selecting_options' and self.current_turn_player == self.players[addr]:
                    self.set_timer(0)
            elif data.data_type == 'accept':
                if self.state == 'selecting_options':
                    if self.current_turn_player == self.players[addr]:
                        self.state = 'drawing'
                        self.current_turn_player.conn.sendall(SocketData(data_type='drawing'))
                        for player in self.players.values():
                            if player != self.current_turn_player:
                                player.conn.sendall(SocketData(data_type='guessing'))
                        self.set_timer(GameModel.drawing_time)
                        self.broadcast(SocketData(data_type='set_time', time=self.timer))
                
    def get_current_turn_packet(self, addr):
        with self.players_lock:
            if self.state == 'waiting_to_start':
                return SocketData(data_type='waiting_to_start')
            elif self.state == 'selecting_options':
                return SocketData(data_type='selecting_options', user_id=self.current_turn_player.user_id, user_name=self.current_turn_player.name)
            elif self.state == 'drawing':
                if self.current_turn_player.addr == addr:
                    return SocketData(data_type='drawing')
                return SocketData(data_type='guessing')
            elif self.state == 'waiting':
                return SocketData(data_type='waiting')
            elif self.state == 'finished':
                return SocketData(data_type='finished')
            return SocketData(data_type='guessing')

    def checking_turn(self, addr):
        with self.players_lock:
            if self.current_turn_player is None:
                return False

            if self.current_turn_player.addr == addr:
                return True

    def register_client(self, addr, client: MySocket):
        try:
            with self.players_lock:
                if addr in self.players:
                    return False

                # create a thread to handle client
                request = client.recv()
                if request.data_type != 'register_request':
                    return False

                with self.id_generator_lock:
                    self.players[addr] = Player(addr, client, request.user_name, self.create_id())
                    self.players[addr].conn.sendall(SocketData(data_type='register_response', user_id=self.players[addr].user_id))

                thread = threading.Thread(target=self.handle_client, args=(addr, client))
                thread.daemon = True
                thread.start()
                
                print(f'{addr} joined')
                return True
        except Exception as e:
            print(e)
            return False
    
    def unregister_client(self, addr):
        with self.players_lock:
            if addr not in self.players:
                return
            
            del self.players[addr]  
    
    def broadcast(self, data):
        with self.players_lock:
            for player in self.players.values():
                try:
                    player.conn.sendall(data)
                finally:
                    pass
    
    def create_id(self):
        res = self.ids
        self.ids += 1
        return res
    
    def handle_client(self, addr, client: MySocket):
        while True:
            try:
                data = client.recv()
                # deserialize the data
                if not data:
                    break

                self.submit_data(addr, data)
                print(data)
            except Exception as e:
                print(e)
                break

        print(f'{addr} left')
        user_name = self.players[addr].name
        self.unregister_client(addr)
        leave_message = SocketData(data_type='message', message=f'{user_name} 離開了遊戲.')
        self.broadcast(leave_message)
        self.broadcast(SocketData(data_type='user_list', user_list=self.get_user_list()))
        
    