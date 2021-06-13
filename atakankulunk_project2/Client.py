from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QCheckBox, QHeaderView, QMessageBox, \
    QLineEdit, QLabel, QHBoxLayout, QFrame, QSplitter, QListWidget
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from urllib.parse import urlparse, urljoin
import threading
from socket import AF_INET, socket, SOCK_STREAM
import sys

# PROTOCOLS
USERNAME = "USERNAME\n"
MESSAGE = "MESSAGE\n"
QUIT = "QUIT\n"

ANONYMOUS = "ANONYMOUS\n"
SERVER = "SERVER\n"

HOST = "127.0.0.1"
PORT = 5252
ADDR = (HOST, PORT)

BUFSIZE = 1024


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title = 'Atakan ChatRoom'
        self.setFixedSize(1000, 400)
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.window = Window()
        self.setCentralWidget(self.window)
        self.show()

    # Close event overrided - Pencere kapandığında socketi kapatmamız lazım
    def closeEvent(self, event):
        self.window.quit()


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.username = None
        self.first_control = True
        self.clients_usernames = []
        self.current_user = None
        self.chat_dictionary = {}
        self.threadpool = QThreadPool()

        self.connect_server()
        self.init_ui()

    def init_ui(self):
        self.hbox = QHBoxLayout(self)
        self.set_frames()
        self.set_label_and_buttons()
        self.set_user_list()
        self.show()

    # Setting up some UI
    def set_label_and_buttons(self):
        # Username edittext
        self.username_text = QLineEdit(self.top_left_frame)
        self.username_text.setPlaceholderText("Username")
        self.username_text.move(15, 20)
        self.username_text.resize(100, 30)

        # Join button to join chat
        self.join_button = QPushButton('Katıl', self.top_left_frame)
        self.join_button.clicked.connect(self.set_username)
        self.join_button.move(120, 20)
        self.join_button.resize(50, 30)

        # Message edittext to write to chat
        self.message_text = QLineEdit(self.right_frame)
        self.message_text.setPlaceholderText("type_here")
        self.message_text.move(10, 220)
        self.message_text.resize(200, 40)

        # Send button to send message
        self.send_button = QPushButton('Ozel Gonder', self.right_frame)
        self.send_button.clicked.connect(self.send_message)
        self.send_button.move(220, 220)
        self.send_button.resize(80, 40)

        self.send_button2 = QPushButton('Genel Gonder', self.right_frame)
        self.send_button2.clicked.connect(self.send_messageGenel)
        self.send_button2.move(320, 220)
        self.send_button2.resize(100, 40)

        self.chatlist = QListWidget(self.right_frame)
        self.chatlist.addItem('test')
        self.chatlist.clear()

        self.chatlist2 = QListWidget(self.right_frame)
        self.chatlist2.addItem('test')
        self.chatlist2.move(270, 0)
        self.chatlist2.resize(300, 190)
        self.chatlist2.clear()


    # When quiting from server - This works when user close the window
    def quit(self):
        if self.username != None:
            self.username = "ANONYMOUS\n"

        FROM = self.username
        TO = SERVER
        PROTOCOL = QUIT
        MESSAGE = PROTOCOL + FROM + TO + MESSAGE
        self.client_socket.send(bytes(MESSAGE, 'utf8'))
        print("Connection Closed!")

    def set_user_list(self):
        self.users_list = QListWidget(self.bottom_left_frame)
        self.users_list.itemClicked.connect(self.user_on_click)
        self.users_list.setMinimumSize(10, 15)

    def user_on_click(self):

        # If this is first click, we need to store current user
        if self.first_control:
            self.current_user = self.users_list.currentItem().text()

            if self.is_user_recorded(self.current_user):
                print(self.chat_dictionary[self.current_user])

            if not self.is_user_recorded(self.current_user):
                self.create_record(self.current_user)

            for i in self.chat_dictionary[self.current_user]:
                self.chatlist.addItem(i)
            self.first_control = False
        else:
            messages = [self.chatlist.item(i).text() for i in range(self.chatlist.count())]
            self.chat_dictionary[self.current_user] = messages
            self.current_user = self.users_list.currentItem().text()
            self.chatlist.clear()

            if not self.is_user_recorded(self.current_user):
                self.create_record(self.current_user)

            for i in self.chat_dictionary[self.current_user]:
                self.chatlist.addItem(i)

    # Create user record
    def create_record(self, user):
        self.chat_dictionary[user] = []

    # Setting frame for three partial
    def set_frames(self):
        self.top_left_frame = QFrame()
        self.top_left_frame.setFrameShape(QFrame.StyledPanel)

        self.bottom_left_frame = QFrame()
        self.bottom_left_frame.setFrameShape(QFrame.StyledPanel)

        self.right_frame = QFrame()
        self.right_frame.setFrameShape(QFrame.StyledPanel)

        self.splitter1 = QSplitter(Qt.Vertical, frameShape=QFrame.StyledPanel)
        self.splitter1.addWidget(self.top_left_frame)
        self.splitter1.addWidget(self.bottom_left_frame)
        self.splitter1.setSizes([125, 400])

        self.splitter2 = QSplitter(Qt.Horizontal, frameShape=QFrame.StyledPanel)
        self.splitter2.addWidget(self.splitter1)
        self.splitter2.addWidget(self.right_frame)
        self.splitter2.setSizes([200, 350])

        self.hbox.addWidget(self.splitter2)

    # Connecting server before everything
    def connect_server(self):

        self.client_socket = socket(AF_INET, SOCK_STREAM)
        try:
            self.client_socket.connect(ADDR)
        except Exception as e:
            print("Couldn't connect to server : ", e)
        else:
            connection_message = self.client_socket.recv(BUFSIZE).decode("utf8")
            print(connection_message)

    # Setting username and waiting for it's validation. After that, start message receive handler
    def set_username(self):
        username = self.username_text.text()
        # control eklenecek
        if username == "":
            return

        PROTOCOL = USERNAME
        FROM = ANONYMOUS
        TO = SERVER
        TEXT = username
        PACKET = PROTOCOL + FROM + TO + TEXT

        self.client_socket.send(bytes(PACKET, "utf8"))

        validation = self.client_socket.recv(BUFSIZE).decode("utf8")
        if validation == "True":
            self.disable_options()
            self.username = username
            self.handler = Handler(self.client_socket)
            self.handler.signals.update_usernames.connect(self.update_username_list)
            self.handler.signals.chat_message.connect(self.write_list)
            self.threadpool.start(self.handler)
            self.handler.signals.chat_message2.connect(self.write_GENEL)

    # Disabling join options when username validated
    def disable_options(self):
        self.username_text.setDisabled(True)
        self.join_button.setDisabled(True)

    # Updating username list when they recevied
    def update_username_list(self, usernames):
        self.users_list.clear()
        for i in usernames:
            if i not in self.clients_usernames and i != self.username:
                self.users_list.addItem(i)

    # Write chat list
    def write_list(self, person, message):
        if self.is_user_recorded(person):
            self.update_record(person, message)
            if self.is_window_active(person):
                self.chatlist.addItem(person + message)
        else:
            self.chat_dictionary[person] = [person + message]

    # If message came in and it's not in active window, update it from backround
    def update_record(self, user, msg):
        value = self.chat_dictionary[user]
        print(type(value), value)
        value.append(user + msg)
        self.chat_dictionary[user] = value

    # Return True if window is active
    def is_window_active(self, user):
        return self.current_user == user

    # Return True if user is recorded
    def is_user_recorded(self, user):
        users = self.chat_dictionary.keys()
        if user in users:
            return True
        else:
            return False

    def send_messageGenel(self):
        text = self.message_text.text()
        PROTOCOL = 'GENEL+\n'
        FROM = self.username + "\n"
        TO = 'GENEL' + "\n"
        TEXT = ": " + text
        PACKET = PROTOCOL + FROM + TO + TEXT

        self.client_socket.send(bytes(PACKET, "utf8"))
        self.message_text.clear()
        print("MESSAGE SENDED")


    def write_GENEL(self,fr, msg):
        mes = str(fr + ":" + msg)
        self.chatlist2.addItem(mes)




    # Sending message
    def send_message(self):
        text = self.message_text.text()
        if text != "" and text != None:
            if self.users_list.currentItem() == None:
                print("Please select user to send message")
                return
            PROTOCOL = MESSAGE
            FROM = self.username + "\n"
            TO = self.current_user + "\n"
            TEXT = ": " + text
            PACKET = PROTOCOL + FROM + TO + TEXT

            self.client_socket.send(bytes(PACKET, "utf8"))
            self.chatlist.addItem('You' + TEXT)
            self.message_text.clear()
            print("MESSAGE SENDED")


class HandlerSignals(QObject):
    chat_message = pyqtSignal(str, str)
    chat_message2 = pyqtSignal(str, str)
    update_usernames = pyqtSignal(list)


class Handler(QRunnable):
    def __init__(self, connection):
        super(Handler, self).__init__()
        self.connection = connection
        self.signals = HandlerSignals()
        self.chatlist = {}
        self.clients = []

    @pyqtSlot()
    def run(self):
        self.recv_messages()

    def recv_messages(self):
        while True:
            received_message = self.connection.recv(BUFSIZE).decode("utf8")
            print("INCOMING MESSAGE")
            message = received_message.split("\n")

            if "GENEL" in message[0]:
                FROM = message[1]
                TO = message[2]
                MSG = ' '.join(message[3:])
                self.signals.chat_message2.emit(str(FROM), str(MSG))


            if message[0] == "INFO":
                usernames = message[3].split("-")
                self.clients.clear()
                for u in usernames:
                    self.clients.append(u)
                self.signals.update_usernames.emit(self.clients)

            if message[0] == "MESSAGE":
                FROM = message[1]
                TO = message[2]
                MSG = ' '.join(message[3:])
                self.signals.chat_message.emit(str(FROM), str(MSG))




if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
