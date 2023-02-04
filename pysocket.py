import logging
import random
import socket
import sys
import threading
import tkinter

import select
from tkinter import simpledialog, messagebox
from tkinter import *
from tkinter import ttk
from time import sleep
from themes import Modern


class Server:
    room_name = ''
    active_conns = []
    connections = {None: {'name': 'ryan', 'color': '#000000'}}

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def launch(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((self.host, self.port))
            sock.listen()
            sock.setblocking(FALSE)

            read_socket_list = [sock]
            write_socket_list = [sock]

            while True:
                receivable, writeable, err = select.select(read_socket_list, write_socket_list, [], 1)

                if end_signal.is_set():
                    logging.warning("[SIGEND] Server closing head")
                    return SIGEND

                for r in receivable:
                    if r == sock:
                        conn, addr = sock.accept()
                        print(conn)
                        self.active_conns.append(conn)

                        print(f"[Server] Connected: {conn}")
                        conn_thread = threading.Thread(target=self.listen, args=(conn,))
                        conn_thread.start()

    def listen(self, conn):
        conn.sendall(f"Welcome to PyChat! (name:{self.room_name} | users:{len(self.active_conns)})".encode())
        conn.setblocking(TRUE)
        initialized = FALSE

        while True:
            data = conn.recv(1024)

            if (not initialized) and int(data.decode()[0]) == int(SIGCONFIG):
                initialized = TRUE
                unpacked_data = f"{data.decode()[1:]}".split(',')
                self.connections[conn] = {'name': unpacked_data[0], 'color': unpacked_data[1]}
                print(f"[SIGCONFIG] Connection: {self.connections[conn]}")

                for c in self.active_conns:
                    c.sendall(f"[Server] [{self.connections[conn]['name']}] joined!".encode())
                continue

            if not data:
                logging.warning("[Server] Client disconnected...")
                return SIGEND

            if end_signal.is_set() or data == SIGEND:
                logging.warning("[SIGEND] Server closing tail")
                return SIGEND

            if not initialized:
                continue

            for c in self.active_conns:
                c.sendall(f"[{self.connections[conn]['name']}] ".encode() + data)


class Client:
    class Config:
        name = ''

        def __init__(self, name='default', color='#default'):
            self.name = name
            if color == "#default":
                self.randomize_color()
            else:
                self.color = color

        def randomize_color(self):
            self.color = f'#{hex(random.randint(50, 255))[2:]}{hex(random.randint(50, 255))[2:]}{hex(random.randint(50, 255))[2:]}'.upper()

    def __init__(self, host_addr='127.0.0.1', port_num=8080, config=None):
        self.host_addr = host_addr
        self.port_num = port_num
        self.config = self.Config()

    def launch(self, name):
        print(name)
        self.config.name = name

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.host_addr, self.port_num))
            sock.sendall(SIGCONFIG + self.config.name.encode() + b"," + self.config.color.encode())

            sock.setblocking(FALSE)

            read_socket_list = [sock]
            write_socket_list = [sock]

            while True:
                receivable, writeable, err = select.select(read_socket_list, write_socket_list, [], 1)

                if end_signal.is_set():
                    sock.sendall(SIGEND)
                    logging.warning("[SIGEND] Closing client")
                    sleep(1)
                    return

                for r in receivable:
                    if r == sock:
                        data = sock.recv(1024)

                        if not data:
                            break

                        sender = data.decode()[1:].split(']')[0]

                        if sender == self.config.name:
                            ui.chat_output.tag_config('client_color', foreground=self.config.color)
                            ui.chat_output.insert('end', data.decode() + "\n", 'client_color', )
                        else:
                            ui.chat_output.insert('end', data.decode() + "\n")

                for w in writeable:
                    if w == sock:
                        if ui.buffered_input != "":
                            sock.sendall(ui.buffered_input.encode())
                            ui.buffered_input = ""


host = '127.0.0.1'
port = 8080

HOST = b'0'
CLIENT = b'1'
SIGCONFIG = b'8'
SIGEND = b'-1'

server = Server(host, port)
client = Client(host, port)

server_thread = threading.Thread(target=server.launch)
client_thread = threading.Thread(target=client.launch, args=(client.config.name,))
end_signal = threading.Event()


def start_host(name):
    global client_thread
    client_thread = threading.Thread(target=client.launch, args=(name,))

    server.room_name = tkinter.simpledialog.askstring("Room Name", "Enter a room name:")
    ui.open_content()

    server_thread.start()

    sleep(1)

    client_thread.start()


def start_join(name):
    global client_thread
    client_thread = threading.Thread(target=client.launch, args=(name,))

    ui.open_content()

    client_thread.start()


def on_quit(root):
    global end_signal
    confirmation = messagebox.askyesno("Quit?", "Do you want to end the connection and quit?")

    if confirmation:
        end_signal = threading.Event()
        end_signal.set()
        if client_thread.is_alive():
            client_thread.join(3)
            logging.warning('Client thread joined')
        if server_thread.is_alive():
            server_thread.join(3)
            if server_thread.is_alive():
                # sys.exit(server_thread)
                logging.warning('Server thread forcibly terminated')
            else:
                logging.warning('Server thread joined')
        root.destroy()


def update_buffer(msg):
    ui.buffered_input = msg
    ui.name = ""
    ui.chat_input.delete(0, len(ui.buffered_input))
    print(f"Buffer updated: {ui.buffered_input}")


class UI:
    buffered_input = ""
    name_input = ""
    chat_input = ""
    chat_output = ""

    def __init__(self, root_name='', menu=''):
        self.root_name = root_name
        self.root = Tk('modern')
        self.menu = ttk.Frame(self.root)
        self.content = ttk.Frame(self.root)

    def create(self):
        # region Window Setup
        root = self.root
        menu = self.menu
        content = self.content

        root.geometry("1280x720")
        theme = Modern(root)
        root.configure(background=theme.bg_color)

        style = theme.get_style()
        style.theme_use(theme.get_name())
        # endregion

        # region Menu Setup (Page 1)
        menu.configure(style=theme.elements['body'])

        header = ttk.Label(menu, text="PySocket")
        header.configure(style=theme.elements['h1'])

        name_entry = ttk.Frame(menu, width=50, padding=20)
        name_entry.configure(style=theme.elements['entry'])
        self.name_input = ttk.Entry(name_entry, background='#aaaaaa', font=(theme.font, 16))
        self.name_input.configure(style=theme.elements['input'])

        host_button = ttk.Button(menu, text="Host", command=lambda: start_host(self.name_input.get()))
        host_button.configure(style=theme.elements['button-large'])

        join_button = ttk.Button(menu, text="Join", command=lambda: start_join(self.name_input.get()))
        join_button.configure(style=theme.elements['button-large'])

        menu.grid()
        root.columnconfigure(menu, weight=1)
        root.rowconfigure(menu, weight=1)
        menu.grid(column=0, row=0)
        header.grid(column=0, row=0, pady='0 20')
        name_entry.grid(column=0, row=1, sticky='nswe', pady='0 80')
        self.name_input.grid(column=0, row=1, sticky='nswe')
        host_button.grid(column=0, row=2, pady='0 30')
        join_button.grid(column=0, row=3, pady='0 30')
        # endregion

        # region Content Setup (Page 2)
        content.configure(style=theme.elements['body'])

        header = ttk.Label(content, text="PySocket")
        header.configure(style=theme.elements['h1'])

        chat_entry = ttk.Frame(content, width=50, padding=20)
        chat_entry.configure(style=theme.elements['entry'])
        self.chat_input = ttk.Entry(chat_entry, background='#aaaaaa', font=(theme.font, 16))
        self.chat_input.configure(style=theme.elements['input'])

        send_button = ttk.Button(content, text="send", command=lambda: update_buffer(self.chat_input.get()))
        send_button.configure(style=theme.elements['button'])

        self.chat_output = Text(content, background=theme.mg_color, foreground=theme.fg_color, font=(theme.font, 16),
                                relief='flat', width=40, height=15, padx=18, pady=22)

        header.grid(column=0, row=0, sticky='n')
        self.chat_output.grid(column=0, row=1, sticky='nswe')
        chat_entry.grid(column=0, row=2, sticky='nswe')
        self.chat_input.grid(column=0, row=2, sticky='nswe')
        send_button.grid(column=0, row=2, sticky='nse')
        # endregion

        root.protocol('WM_DELETE_WINDOW', lambda: on_quit(root))
        root.mainloop()

    def open_content(self):
        self.menu.grid_forget()
        self.content.grid()

        self.root.columnconfigure(self.content, weight=1)
        self.root.rowconfigure(self.content, weight=1)


ui = UI('PyChat')
ui.create()
