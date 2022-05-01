import time
from kivy.config import Config
Config.set('graphics', 'resizable', False)
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse, Line
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.audio import SoundLoader
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scatterlayout import ScatterLayout

import pickle
import threading

from MySocket import MySocket, SocketData



class SoundEffect:

    _message_sound = SoundLoader.load('./sound/messageSound.wav')
    _button_sound_1 = SoundLoader.load('./sound/buttonSound1.wav')
    _correct_sound = SoundLoader.load('./sound/correct.wav')
    _select_sound = SoundLoader.load('./sound/select.wav')
    _answer_sound = SoundLoader.load('./sound/answer.wav')
    def __init__(self, filename):
        pass
    
    @staticmethod
    def init():
        SoundEffect._message_sound.loop = False
        SoundEffect._message_sound.volume = 1
        SoundEffect._message_sound.seek(0)
        SoundEffect._button_sound_1.loop = False
        SoundEffect._button_sound_1.volume = 1
        SoundEffect._button_sound_1.seek(0)
        SoundEffect._correct_sound.loop = False
        SoundEffect._correct_sound.volume = 1
        SoundEffect._correct_sound.seek(0)
        SoundEffect._select_sound.loop = False
        SoundEffect._select_sound.volume = 1
        SoundEffect._select_sound.seek(0)
        SoundEffect._answer_sound.loop = False
        SoundEffect._answer_sound.volume = 1
        SoundEffect._answer_sound.seek(0)

    @staticmethod
    def play_message_sound():
        SoundEffect._message_sound.play()
        SoundEffect._message_sound.seek(0)
    
    @staticmethod
    def play_button_sound_1():
        SoundEffect._button_sound_1.play()
        SoundEffect._message_sound.seek(0)
    
    @staticmethod
    def play_correct_sound():
        SoundEffect._correct_sound.play()
        SoundEffect._correct_sound.seek(0)

    @staticmethod
    def play_select_sound():
        SoundEffect._select_sound.play()
        SoundEffect._select_sound.seek(0)
    
    @staticmethod
    def play_answer_sound():
        SoundEffect._answer_sound.play()
        SoundEffect._answer_sound.seek(0)


class MouseCursor(ScatterLayout):
    cursor_size = (60, 60)
    def __init__(self) -> None:
        super().__init__()
        # draw a circle
        with self.canvas:
            Color(0.3, 0.3, 0.3, 0.7)
            self.size_hint = (None, None)
            self.rect = Ellipse(size=MouseCursor.cursor_size, pos=self.pos)
        self.bind(pos=self.update_rect)
        self.size_hint = (None, None)
        Window.bind(mouse_pos=self.on_mouse_pos)
    
    def on_mouse_pos(self, *args):
        if self.rect.size != MouseCursor.cursor_size:
            self.rect.size = MouseCursor.cursor_size
        self.rect.pos = (args[1][0] - MouseCursor.cursor_size[0] / 2, args[1][1] - MouseCursor.cursor_size[1] / 2)

    
    def on_touch_down(self, touch):
        pass
    
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        

client_socket = None

class ScrollableLabel(ScrollView):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # ScrollView does not allow us to add more than one widget, so we need to trick it
        # by creating a layout and placing two widgets inside it
        # Layout is going to have one collumn and and size_hint_y set to None,
        # so height wo't default to any size (we are going to set it on our own)
        self.layout = GridLayout(cols=1, size_hint_y=None)
        self.add_widget(self.layout)

        # Now we need two widgets - Label for chat history and 'artificial' widget below
        # so we can scroll to it every new message and keep new messages visible
        # We want to enable markup, so we can set colors for example
        self.chat_history = Label(size_hint_y=None, markup=True, font_name='msjh.ttc', color=(0, 0, 0, 1))
        self.scroll_to_point = Label(color=(0, 0, 0, 1))

        # We add them to our layout
        self.layout.add_widget(self.chat_history)
        self.layout.add_widget(self.scroll_to_point)

    def clear_chat_history(self):
        self.chat_history.text = ''

    # Method called externally to add new message to the chat history
    def update_chat_history(self, message):

        # First add new line and message itself
        self.chat_history.text += '\n' + message

        # Set layout height to whatever height of chat history text is + 15 pixels
        # (adds a bit of space at teh bottom)
        # Set chat history label to whatever height of chat history text is
        # Set width of chat history text to 98 of the label width (adds small margins)
        self.layout.height = self.chat_history.texture_size[1] + 15
        self.chat_history.height = self.chat_history.texture_size[1]
        self.chat_history.text_size = (self.chat_history.width * 0.98, None)

        # As we are updating above, text height, so also label and layout height are going to be bigger
        # than the area we have for this widget. ScrollView is going to add a scroll, but won't
        # scroll to the botton, nor is there a method that can do that.
        # That's why we want additional, empty widget below whole text - just to be able to scroll to it,
        # so scroll to the bottom of the layout
        self.scroll_to(self.scroll_to_point)


class GameGrid(GridLayout):

    class TopBar(BoxLayout):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.orientation = 'horizontal'
            self.game_name_label = Label(text='[b]你畫我猜 Guess and Draw![/b]', markup=True, font_size=30, font_name='msjh.ttc')

            self.button_group_grid = BoxLayout(orientation='horizontal')
            self.exit_button = Button(text='退出 Exit', font_size=20, font_name='msjh.ttc', background_normal='', background_color=(0.5, 0.5, 0.5, 1))
            self.button_group_grid.add_widget(self.exit_button)
            self.exit_button.bind(on_release=self.on_exit_button)
            self.spacing = 200

            self.add_widget(self.game_name_label)
            self.add_widget(self.button_group_grid)
        def on_exit_button(self, instance):
            try:
                #SoundEffect.play_button_sound_1()
                client_socket.close()
            finally:
                app.screen_manager.current = 'menu'

    class UserListScroll(ScrollView):
        
        class UserInfo(GridLayout):
            def __init__(self, name, point, **kwargs) -> None:
                super(GameGrid.UserListScroll.UserInfo, self).__init__(**kwargs)
                self.rows = 2
                self.padding = 5
                self.height = 70
                with self.canvas.before:
                    Color(1, 1, 1, 1)
                    self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[(10, 10), (10, 10), (10, 10), (10, 10)])
                self.bind(size=self._update_rect, pos=self._update_rect)

                self.add_widget(Label(text=name, color=(0, 0, 0, 1), font_name='msjh.ttc'))
                self.add_widget(Label(text=f'Points: {point}', color=(0, 0, 0, 1), font_name='msjh.ttc'))
            
            def _update_rect(self, instance, value):
                self.rect.size = instance.size
                self.rect.pos = instance.pos

        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            with self.canvas.before:
                Color(0, 0.5, 1, 0.7)
                self.rect = self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[(5, 5), (5, 5), (5, 5), (5, 5)])
            self.bind(size=self._update_rect, pos=self._update_rect)
            self.user_list = []
            self.layout = GridLayout(cols=1, size_hint_y=None)
            self.layout.spacing = 5
            self.layout.padding = 10
            self.padding = 5
            self.layout.bind(minimum_height=self.layout.setter('height'))
            self.add_widget(self.layout)
        
        def set_user_list(self, user_list):
            self.layout.clear_widgets()
            self.user_list = sorted(user_list, key=lambda x: x[1], reverse=True)
            for user in self.user_list:
                user_info = GameGrid.UserListScroll.UserInfo(user[0], user[1])
                user_info.size_hint = (1, None)
                self.layout.add_widget(user_info)
        
        def _update_rect(self, instance, value):
            self.rect.size = instance.size
            self.rect.pos = instance.pos

    class DrawingAndChat(BoxLayout):
        def __init__(self, **kwargs):
            super(GameGrid.DrawingAndChat, self).__init__(**kwargs)
            self.padding = 20
            self.orientation = 'vertical'
            self.drawing = GameGrid.Drawing()
            self.chat = GameGrid.Chat()
            self.time_bar = ProgressBar(max=10, value=0, size_hint=(1, None))
            self.time_bar_lock = threading.Lock()

            time_thread = threading.Thread(target=self._run_timer)
            time_thread.daemon = True
            time_thread.start()

            self.drawing.size_hint_y = 0.7
            self.time_bar.size_hint_y = 0.05
            self.chat.size_hint_y = 0.25
            self.spacing = 20

            self.add_widget(self.drawing)
            self.add_widget(self.time_bar)
            self.add_widget(self.chat)
        
        def set_timer(self, seconds):
            with self.time_bar_lock:
                self.time_bar.max = seconds
                self.time_bar.value = seconds

        def _run_timer(self):
            while True:
                time.sleep(0.1)
                with self.time_bar_lock:
                    if self.time_bar.value - 0.1 >= 0:
                        self.time_bar.value -= 0.1
                    else:
                        self.time_bar.value = 0

    class Chat(GridLayout):
        def __init__(self, **kwargs) -> None:
            super(GameGrid.Chat, self).__init__(**kwargs)

            with self.canvas.before:
                Color(1, 1, 1, 1)
                self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[(10, 10), (10, 10), (0, 0), (0, 0)])
            self.bind(size=self._update_rect, pos=self._update_rect)
            self.spacing = 5
            self.text_input = TextInput(text='',
                multiline=False, 
                font_size=15, 
                size_hint_y=0.3, 
                height=35, 
                text_validate_unfocus=False,
                font_name='msjh.ttc')

            self.scrollable_label = ScrollableLabel()
            self.text_input.on_text_validate = self.send_message
            self.rows = 2
            self.add_widget(self.scrollable_label)
            self.add_widget(self.text_input)

        def clear_chat(self):
            self.scrollable_label.clear_chat_history()

        def add_message(self, message):
            self.scrollable_label.update_chat_history(message)

        def send_message(self):
            if self.text_input.text == '':
                return
            data = SocketData(data_type='message', message=self.text_input.text)
            client_socket.sendall(data)
            self.text_input.text = ''
        
        def _update_rect(self, instance, value):
            self.rect.size = instance.size
            self.rect.pos = instance.pos

    class Drawing(GridLayout):
        
        current_color = (1, 0, 0, 1)
        thickness = 1

        class ColorPlate(BoxLayout):
            def __init__(self, **kwargs):
                super(GameGrid.Drawing.ColorPlate, self).__init__(**kwargs)

                # set background color to white
                with self.canvas.before:
                    Color(1, 1, 1, 1)
                    self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[(10, 10), (10, 10), (10, 10), (10, 10)])
                self.bind(size=self._update_rect, pos=self._update_rect)
                self.orientation = 'vertical'
                self.spacing = 5
                colors = [
                    (0, 0, 0), 
                    (1, 0, 0), 
                    (0, 1, 0), 
                    (0.4, 0.7, 1),
                    (1, 1, 0),
                    (1, 0, 1),
                    (0, 0.47, 1),
                    (0, 1, 1),
                    (1, 0.6, 0), 
                    (0.5, 0, 0),
                    (0, 0.5, 0), 
                    (0, 0, 0.5), 
                    (0.5, 0.5, 0), 
                    (0.5, 0, 0.5), 
                    (0, 0.5, 0.5), 
                    (0.5, 0.5, 0.5)
                ]

                def set_color(instance):
                    GameGrid.Drawing.current_color = tuple(instance.background_color)
                
                def set_thickness(*args):
                    GameGrid.Drawing.thickness = self.slider.value
                    self.slider.cursor_size = (GameGrid.Drawing.thickness*5, GameGrid.Drawing.thickness*5)
                    MouseCursor.cursor_size = (GameGrid.Drawing.thickness*5, GameGrid.Drawing.thickness*5)

                self.plate_grid = GridLayout(rows=9, cols=2, spacing=5, padding=20)
                for i in range(len(colors)):
                    btn = Button(background_color=colors[i], background_normal='', size_hint=(None, None), height=15, width=15)
                    btn.bind(on_press=set_color)
                    self.plate_grid.add_widget(btn)

                self.tool_grid = BoxLayout(orientation='horizontal', spacing=5)
                self.slider = Slider(min=0.5, max=5, value=1, orientation='vertical', step=0.5, value_track=True, value_track_color=[0.5, 0.5, 0.5, 1])
                self.slider.cursor_size = (GameGrid.Drawing.thickness*5, GameGrid.Drawing.thickness*5)
                # self.slider.background_width = 100
                self.slider.bind(value=set_thickness)
                self.eraser_button = Button(text='', size_hint=(None, None), height=24, width=24, background_normal='imgs/eraser.png', background_color=(1,1,1))
                self.eraser_button.bind(on_press=set_color)
                self.tool_grid.add_widget(self.slider)
                self.tool_grid.add_widget(self.eraser_button)

                self.add_widget(self.plate_grid)
                self.add_widget(self.tool_grid)
            
            def _update_rect(self, instance, value):
                self.rect.size = instance.size
                self.rect.pos = instance.pos

        class Board(GridLayout):

            class FinishedScreen(BoxLayout):
                def __init__(self, **kwargs):
                    super(GameGrid.Drawing.Board.FinishedScreen, self).__init__(**kwargs)
                    self.orientation = 'horizontal'
                    self.first_player_name = Label(text='', font_size=50, height=40, font_name='msjh.ttc', color=[0.73, 0.57, 0, 1])
                    self.second_player_name = Label(text='', font_size=40, height=40, font_name='msjh.ttc', color=[0.45, 0.45, 0.43, 1])
                    self.third_player_name = Label(text='', font_size=30, height=40, font_name='msjh.ttc', color=[0.7, 0.36, 0.09, 1])

                    # set background color to gray
                    with self.canvas.before:
                        Color(0.7, 0.7, 0.7, 1)
                        self.rect = Rectangle(size=self.size, pos=self.pos)
                    self.bind(size=self._update_rect, pos=self._update_rect)
                    
                    self.add_widget(self.second_player_name)
                    self.add_widget(self.first_player_name)
                    self.add_widget(self.third_player_name)
                
                def set_winners(self, players):
                    self.first_player_name.text = ''
                    self.second_player_name.text = ''
                    self.third_player_name.text = ''
                    try:
                        self.first_player_name.text = '第一名\n'+ players[0][0]
                        self.second_player_name.text = '第二名\n'+ players[1][0]
                        self.third_player_name.text = '第三名\n' + players[2][0]
                        
                    except Exception as e:
                        print(e)
                
                def _update_rect(self, instance, value):
                    self.rect.size = instance.size
                    self.rect.pos = instance.pos


            class LobbyScreen(BoxLayout):
                def __init__(self, **kwargs):
                    super(GameGrid.Drawing.Board.LobbyScreen, self).__init__(**kwargs)
                    self.orientation = 'vertical'
                    self.spacing = 5
                    self.label = Label(text='正在等待遊戲開始...', font_size=35, font_name='msjh.ttc', color=[0.5, 0.5, 0.5, 1])
                    self.add_widget(self.label)
            
            class WaitingScreen(BoxLayout):
                def __init__(self, **kwargs):
                    super(GameGrid.Drawing.Board.WaitingScreen, self).__init__(**kwargs)
                    self.orientation = 'vertical'
                    self.spacing = 20
                    self.current_player = ''
                    self.waiting_label = Label(text='畫家：' + self.current_player + ' 正在選擇...', font_size=35, font_name='msjh.ttc', color=[0.5, 0.5, 0.5, 1])
                    self.add_widget(self.waiting_label)
                
                def set_current_player(self, player):
                    self.current_player = player
                    self.waiting_label.text = '畫家：' + player + ' 正在選擇...'

            class AnswerScreen(BoxLayout):
                def __init__(self, **kwargs):
                    super(GameGrid.Drawing.Board.AnswerScreen, self).__init__(**kwargs)
                    self.orientation = 'vertical'
                    self.answer = ''
                    self.answer_label = Label(text=f'「{self.answer}」', font_size=40, font_name='msjh.ttc', color=[0, 0, 0, 1])
                    self.answer_label.size_hint_y = 0.6
                    self.add_widget(Label(text='正確解答為:', font_size=35, font_name='msjh.ttc', color=[0.5, 0.5, 0.5, 1], size_hint_y=0.4))
                    self.add_widget(self.answer_label)

                def set_answer(self, answer):
                    self.answer = answer
                    self.answer_label.text = f'「{self.answer}」'
            
            class DrawChoiceScreen(BoxLayout):
                def __init__(self, **kwargs):
                    super(GameGrid.Drawing.Board.DrawChoiceScreen, self).__init__(**kwargs)
                    self.orientation = 'vertical'
                    self.spacing = 20
                    self.question = ''
                    self.question_label = Label(text=f'「{self.question}」', font_size=25, font_name='msjh.ttc', color=[0.5, 0.5, 0.5, 1])
                    self.skip_btn = Button(text='跳過', font_size=25, font_name='msjh.ttc', background_color=[0.5, 0.5, 0.5, 1], background_normal='')
                    self.accept_btn = Button(text='開畫', font_size=25, font_name='msjh.ttc', background_color=[0.96, 0.54, 0.25, 1], background_normal='')
                    self.skip_btn.bind(on_press=self.on_skip_button_pressed)
                    self.accept_btn.bind(on_press=self.on_accept_button_pressed)

                    self.button_groups = BoxLayout(orientation='horizontal', spacing=60, padding=25)
                    self.button_groups.add_widget(self.skip_btn)
                    self.button_groups.add_widget(self.accept_btn)

                    self.add_widget(Label(text='你的回合:', font_size=35, font_name='msjh.ttc', color=[0.5, 0.5, 0.5, 1]))
                    self.add_widget(Label(text='題目:', font_size=20, font_name='msjh.ttc', color=[0.5, 0.5, 0.5, 1]))
                    self.add_widget(self.question_label)
                    self.add_widget(self.button_groups)
                
                def on_skip_button_pressed(self, instance):
                    client_socket.sendall(SocketData(data_type='skip'))

                def on_accept_button_pressed(self, instance):
                    client_socket.sendall(SocketData(data_type='accept'))
                
                def set_question(self, question):
                    self.question = question
                    self.question_label.text = f'「{self.question}」'
                

            def __init__(self, **kwargs) -> None:
                super(GameGrid.Drawing.Board, self).__init__(**kwargs)
                self.enable_draw = False
                self.server_line = None
                self.wainting_screen = GameGrid.Drawing.Board.WaitingScreen()
                self.answer_screen = GameGrid.Drawing.Board.AnswerScreen()
                self.draw_choice_screen = GameGrid.Drawing.Board.DrawChoiceScreen()
                self.lobby_screen = GameGrid.Drawing.Board.LobbyScreen()
                self.finished_screen = GameGrid.Drawing.Board.FinishedScreen()
                with self.canvas.before:
                    Color(1, 1, 1, 1)
                    self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[(30, 30), (30, 30), (30, 30), (30, 30)])
                self.bind(size=self._update_rect, pos=self._update_rect)
                self.rows = 1
            
            def switch_to_finished_screen(self, players):
                self.clear_widgets()
                self.finished_screen.set_winners(players)
                self.add_widget(self.finished_screen)

            def switch_to_blank_screen(self):
                self.enable_draw = False
                self.canvas.clear()
                self.clear_widgets()

            def switch_to_lobby_screen(self):
                self.enable_draw = False
                self.canvas.clear()
                self.clear_widgets()
                self.add_widget(self.lobby_screen)
            
            def switch_to_waiting_screen(self):
                self.enable_draw = False
                self.canvas.clear()
                self.clear_widgets()
                self.add_widget(self.wainting_screen)
            
            def switch_to_answer_screen(self, answer):
                self.enable_draw = False
                self.canvas.clear()
                self.clear_widgets()
                self.answer_screen.set_answer(answer)
                self.add_widget(self.answer_screen)
            
            def switch_to_draw_choice_screen(self, question):
                self.enable_draw = False
                self.canvas.clear()
                self.clear_widgets()
                self.add_widget(self.draw_choice_screen)
                self.draw_choice_screen.set_question(question)
            
            def switch_to_drawing_screen(self):
                self.canvas.clear()
                self.enable_draw = True
                self.clear_widgets()

            def on_touch_down(self, touch):
                if self.collide_point(touch.x, touch.y):
                    if self.enable_draw:
                        data = SocketData(
                            data_type='start_draw',
                            x=touch.x - self.x,
                            y=touch.y - self.y,
                            color=GameGrid.Drawing.current_color,
                            thickness=GameGrid.Drawing.thickness * 1.5
                        )
                        client_socket.sendall(data)
                        self.on_touch_move(touch)
                    
                    # pass down touch down event to children, which is the current screen.
                    if len(self.children) > 0:
                        self.children[0].on_touch_down(touch)

            def render_with_socket_data(self, data):
                if data.data_type == 'start_draw':
                    with self.canvas:
                        Color(*data.color)
                        self.server_line = Line(points=(data.x + self.x, data.y + self.y))
                        self.server_line.width = data.thickness * 1.5
                elif data.data_type == 'draw':
                    if self.server_line is not None:
                        self.server_line.points += (self.x + data.x, self.y + data.y)

            def on_touch_move(self, touch):
                if self.collide_point(touch.x, touch.y):
                    if self.enable_draw:
                        data = SocketData(
                            data_type='draw',
                            x=touch.x - self.x,
                            y=touch.y - self.y,
                            color=GameGrid.Drawing.current_color,
                            thickness=GameGrid.Drawing.thickness * 1.5
                        )
                        client_socket.sendall(data)
                    
            def _update_rect(self, instance, value):
                self.rect.pos = instance.pos
                self.rect.size = instance.size

        def __init__(self, **kwargs) -> None:
            super(GameGrid.Drawing, self).__init__(**kwargs)
            self.cols = 2
            self.board = GameGrid.Drawing.Board()
            self.color_plate = GameGrid.Drawing.ColorPlate()
            self.board.size_hint_x = 0.9
            self.color_plate.size_hint_x = 0.1
            self.spacing = 15
            self.add_widget(self.color_plate)
            self.add_widget(self.board)
        
        def on_touch_down(self, touch):
            self.board.on_touch_down(touch)
            self.color_plate.on_touch_down(touch)
        
        def on_touch_move(self, touch):
            if self.board.collide_point(touch.x, touch.y):
                self.board.on_touch_move(touch)


    def __init__(self, **kwargs):
        super(GameGrid, self).__init__(**kwargs)
        with self.canvas.before:
            #Color(0.2, 0.6, 1, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos, source='imgs/gameBackground.png')

        self.bind(size=self._update_rect, pos=self._update_rect)
        self.main_layout = GridLayout(cols=2, spacing=20)
        self.top_bar = GameGrid.TopBar()
        self.top_bar.size_hint_y = 0.05

        self.rows = 2 
        self.user_list = GameGrid.UserListScroll()
        self.drawing_and_chat = GameGrid.DrawingAndChat()

        self.main_layout.add_widget(self.user_list)
        self.main_layout.add_widget(self.drawing_and_chat)
        self.main_layout.size_hint_y = 0.95

        self.padding = (40, 10)
        self.spacing = 10
        self.user_list.size_hint_x = 0.3
        self.add_widget(self.top_bar)
        self.add_widget(self.main_layout)
    
    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size


class LoginMenu(GridLayout):

    def __init__(self, **kwargs):
        super(LoginMenu, self).__init__(**kwargs)
        with self.canvas.before:
            #Color(0.2, 0.6, 1, 0)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, source='imgs/background.png')
        self.bind(size=self._update_rect, pos=self._update_rect)

        self.rows = 3
        self.spacing = 100
        self.padding = 100
        self.title = Label(text='你畫我猜 Draw and Guess!', font_size=50, font_name='msjh.ttc', color=(1, 1, 1, 1))
        self.ip_port_and_user_name_grid = GridLayout(cols=2, spacing=10)
        self.user_name_input = TextInput(hint_text='玩家名稱', font_name='msjh.ttc', multiline=False, font_size=20, text_validate_unfocus=False)
        self.ip_port_text_input = TextInput(hint_text='輸入格式: "IP:PORT"', font_name='msjh.ttc', multiline=False, font_size=20)
        self.login_button = Button(text='連線至伺服器', font_name='msjh.ttc', font_size=20)
        self.title.size_hint_y = 0.6

        self.user_name_input.size_hint_x = 0.3
        self.ip_port_text_input.size_hint_x = 0.7
        self.ip_port_and_user_name_grid.add_widget(self.user_name_input)
        self.ip_port_and_user_name_grid.add_widget(self.ip_port_text_input)
        self.ip_port_and_user_name_grid.spacing = 20
        self.ip_port_and_user_name_grid.size_hint_y = 0.2

        self.login_button.halign = 'center'
        self.login_button.size_hint_y = 0.2
        self.login_button.padding = (100, 0)
        self.login_button.bind(on_press=self.on_login_button_release)

        self.add_widget(self.title)
        self.add_widget(self.ip_port_and_user_name_grid)
        self.add_widget(self.login_button)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
    
    def on_login_button_release(self, instance):
        SoundEffect.play_button_sound_1()
        if self.ip_port_text_input.text == '' or self.user_name_input.text == '':
            return
        # check input format
        try:
            ip, port = self.ip_port_text_input.text.split(':')
            port = int(port)
        except:
            print('Ip and port format is incorrect.')
            return
        
        app.screen_manager.current = 'game'

        try:
            global client_socket
            global user_id
            client_socket = MySocket()
            client_socket.connect((ip, port))
            client_socket.sendall(SocketData(data_type='register_request', user_name=self.user_name_input.text))
            response = client_socket.recv()
            user_id = response.user_id
            data = SocketData(data_type='ready')
            client_socket.sendall(data)
        except Exception as e:
            print(e)
            print('Unable to connect to the server.')
            app.screen_manager.current = 'menu'
            return

        thread = threading.Thread(target=recv_from_server, args=(app,))
        thread.daemon = True
        thread.start()


class MyApp(App):

    def build(self):
        self.title = '你畫我猜 Draw and Guess!'
        self.screen_manager = ScreenManager()
        self.menu_screen = Screen(name='menu')
        self.game_screen = Screen(name='game')
        self.cursor = MouseCursor()
        self.cursor.auto_bring_to_front = True

        self.game_grid = GameGrid()
        self.login_menu = LoginMenu()

        self.menu_screen.add_widget(self.login_menu)
        self.game_screen.add_widget(self.game_grid)
        self.game_screen.add_widget(self.cursor)

        self.screen_manager.add_widget(self.menu_screen)
        self.screen_manager.add_widget(self.game_screen)
        

        return self.screen_manager
    

def recv_from_server(app: MyApp):
    while True:
        try:
            data = client_socket.recv()
            if data:
                if data.data_type == 'draw' or data.data_type == 'start_draw':
                    app.game_grid.drawing_and_chat.drawing.board.render_with_socket_data(data)
                elif data.data_type == 'user_list':
                    app.game_grid.user_list.set_user_list(data.user_list)
                elif data.data_type == 'message':
                    SoundEffect.play_message_sound()
                    if data.message.startswith('正確答案為'):
                        SoundEffect.play_correct_sound()
                    app.game_grid.drawing_and_chat.chat.add_message(data.message)
                elif data.data_type == 'waiting_to_start':
                    app.game_grid.drawing_and_chat.drawing.board.switch_to_lobby_screen()
                    #app.game_grid.drawing_and_chat.set_timer(0)
                elif data.data_type == 'selecting_options':
                    if data.user_id == user_id:
                        SoundEffect.play_select_sound()
                        app.game_grid.drawing_and_chat.drawing.board.switch_to_draw_choice_screen(data.question)
                        #app.game_grid.drawing_and_chat.set_timer(10)
                    else:
                        app.game_grid.drawing_and_chat.drawing.board.wainting_screen.set_current_player(data.user_name)
                        app.game_grid.drawing_and_chat.drawing.board.switch_to_waiting_screen()
                        #app.game_grid.drawing_and_chat.set_timer(10)
                elif data.data_type == 'answer':
                    SoundEffect.play_answer_sound()
                    app.game_grid.drawing_and_chat.drawing.board.switch_to_answer_screen(data.question)
                    #app.game_grid.drawing_and_chat.set_timer(3)
                elif data.data_type == 'waiting':
                    app.game_grid.drawing_and_chat.drawing.board.switch_to_waiting_screen()
                    #app.game_grid.drawing_and_chat.set_timer(10)
                elif data.data_type == 'guessing':
                    app.game_grid.drawing_and_chat.drawing.board.switch_to_blank_screen()
                    #app.game_grid.drawing_and_chat.set_timer(10)
                elif data.data_type == 'drawing':
                    app.game_grid.drawing_and_chat.drawing.board.switch_to_drawing_screen()
                    #app.game_grid.drawing_and_chat.set_timer(10)
                elif data.data_type == 'set_time':
                    app.game_grid.drawing_and_chat.set_timer(data.time)
                elif data.data_type == 'finished':
                    app.game_grid.drawing_and_chat.drawing.board.switch_to_finished_screen(app.game_grid.user_list.user_list)
        except pickle.UnpicklingError:
            print('UnpicklingError')
            pass
        except Exception as e:
            print(e)
            break
    app.screen_manager.current = 'menu'
    app.game_grid.drawing_and_chat.drawing.board.canvas.clear()
    app.game_grid.drawing_and_chat.chat.clear_chat()
    client_socket.close()


if __name__ == '__main__':
    Window.size = (1200, 720)
    MouseCursor.cursor_size = (GameGrid.Drawing.thickness * 5, GameGrid.Drawing.thickness * 5)
    Window.set_system_cursor('crosshair')
    SoundEffect.init()
    user_id = None
    app = MyApp()
    app.run()
    
    
    

    