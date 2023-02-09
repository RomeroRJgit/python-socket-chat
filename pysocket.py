import logging
import random
import socket
import threading
import tkinter
import select
from tkinter import simpledialog, messagebox, filedialog
from tkinter import *
from tkinter import ttk
from time import sleep
import json
import os
import io
import keyboard
from themes import Modern
import events
from themes import EntryXL


def create_packet(data, message=''):
    """Merges an unserialized dict and string to convert into json"""
    if data is None:
        data = {'id': id(data)}
        return json.dumps(data).encode()

    if message != '':
        data['message'] = message
    return json.dumps(data).encode()


def parse_packet(packet):
    """Takes a serialized packet and returns a dictionary if it is a packet"""
    data = packet.decode()
    if len(data) > 0 and data[0] == '{' and data[len(data) - 1] == '}':
        props = json.loads(data)
        return props
    else:
        # Not json format
        return data


class Server:
    room_name = ''
    active_conns = []
    conns_data = []

    def __init__(self, host, port):
        self.room_name = ''
        self.host = host
        self.port = port

    def launch(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((self.host, self.port))
            sock.listen()
            sock.setblocking(False)

            read_socket_list = [sock]
            write_socket_list = [sock]

            while True:
                receivable, writeable, err = select.select(read_socket_list, write_socket_list, [], 1)

                # Thread safe Event signal to close
                if end_signal.is_set():
                    logging.warning("[SIGEND] Server closing head")
                    return SIGEND

                # Waiting for new connections
                for r in receivable:
                    if r == sock:
                        conn, addr = sock.accept()
                        self.active_conns.append(conn)

                        print(f"[Server] Connected: {conn}")
                        conn_thread = threading.Thread(target=self.listen, args=(conn,))
                        conn_thread.start()

    def listen(self, conn):
        server_packet = create_packet(None)
        conn.sendall(server_packet)

        conn.setblocking(1)
        initialized = False

        sleep(0.5)
        while True:
            data = conn.recv(1024)
            packet = parse_packet(data)

            if not initialized and packet:
                initialized = True
                conn.sendall(f"Welcome to PyChat! (name:{self.room_name} | users:{len(self.active_conns)})".encode())

                # packet_dump = json.dumps(packet)
                # self.conns_data.append(packet_dump)
                # self.__save_clients()

                for c in self.active_conns:
                    c.sendall(f"{parse_packet(server_packet)['id']} joined!".encode())
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
                c.sendall(create_packet(packet, message=packet['message']))

    def __save_clients(self):
        with tkinter.filedialog.asksaveasfile() as file:
            file.writelines(f"{self.conns_data}\n")


class Input:
    def __init__(self):
        self.submit = False

    def poll(self):
        self.submit = keyboard.is_pressed(self.submit)


class Client:
    class Config:
        def __init__(self):
            self.cid = -1
            self.name = 'n/a'
            self.color = self.get_random_color()
            self.properties = {'id': -1, 'name': self.name, 'color': self.color}

        @staticmethod
        def get_random_color():
            return f'#{hex(random.randint(50, 255))[2:]}{hex(random.randint(50, 255))[2:]}{hex(random.randint(50, 255))[2:]}'.upper()

        def update(self):
            self.properties = {'id': self.cid, 'name': self.name, 'color': self.color}

    def __init__(self, host_addr='127.0.0.1', port_num=8080, config=None):
        self.host_addr = host_addr
        self.port_num = port_num
        self.config = self.Config()

    def launch(self, name):
        self.config.name = name

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.host_addr, self.port_num))

            self.config.update()
            sock.sendall(create_packet(self.config.properties))

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
                        print(data)

                        # Send Data
                        if isinstance(parse_packet(data), dict):
                            # If packet is from self
                            packet = parse_packet(data)
                            if self.config.cid == -1:
                                self.config.cid = packet['id']
                                continue

                            if packet['name'] == self.config.name:
                                if self.config.cid == -1:
                                    self.config.cid = packet['id']
                                # gui.chat_output.tag_config('self', foreground=packet['color'],
                                # font=('TkDefaultFont', 14, 'bold'))
                                # gui.chat_output.insert('end', f"[{packet['name']}] " + f"{packet['message']}\n", 'self')
                            else:
                                pass
                                # gui.chat_output.tag_config(packet['id'], foreground=packet['color'])
                                # gui.chat_output.insert('end', f"[{packet['name']}] " + f"{packet['message']}\n",
                                # packet['id'])
                            continue
                        else:
                            # If packet is from server
                            # gui.chat_output.insert('end', "[Server] " + data.decode() + "\n")
                            events.broadcast(events.Events.RECEIVE_CHAT, "hello")
                            continue

                for w in writeable:
                    if keyboard.is_pressed('escape'):
                        # gui.root.focus_force()
                        continue
                    if keyboard.is_pressed('enter'):
                        events.broadcast(events.Events.SEND_CHAT, "hi")
                        # update_buffer(gui.chat_input.get_valid_input())

                    # if w == sock:
                    # if gui.buffered_input != "":
                    # self.config.update()
                    # sock.sendall(create_packet(self.config.properties, message=gui.buffered_input))
                    # gui.buffered_input = ""


host = '127.0.0.1'
port = 8080

HOST = b'0'
CLIENT = b'1'
SIGCONFIG = b'8'
SIGEND = b'-1'

server = Server(host, port)
client = Client(host, port)

server_thread = threading.Thread(target=server.launch)
client_thread = threading.Thread(target=client.launch)
end_signal = threading.Event()


def start_host(name):
    global client_thread

    addr = tkinter.simpledialog.askstring("Room Address", "Enter a room address (blank for localhost)")
    if addr != '':
        client.host_addr = addr

    client.config.name = "Ryan"
    client_thread = threading.Thread(target=client.launch, args=(name,))

    server.room_name = tkinter.simpledialog.askstring("Room Name", "Enter a room name:")
    events.broadcast(events.Events.START_CHAT)

    server_thread.start()

    sleep(1)

    client_thread.start()


def start_join(name, addr):
    global client_thread
    addr = tkinter.simpledialog.askstring("Room Address", "Enter a room address (blank for localhost)")
    if addr != '':
        server.host = client.host_addr = addr

    client_thread = threading.Thread(target=client.launch, args=(name,))
    events.broadcast(events.Events.START_CHAT)

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

class Chat:
    def __init__(self):
        self.chat_input = ""
        self.chat_output = ""

        events.register(events.Events.SEND_CHAT, target=self.set_input)

    def set_input(self, msg):
        self.chat_input = msg

    def set_output(self, msg):
        self.set_output = msg
        print(msg)
        #gui.pages['menu'].chat_output = self.set_output


class PySocketWindow:
    theme = None

    class Page(ttk.Frame):
        def __init__(self, master=None, theme=None, **kw):
            super().__init__(master)
            self.root = master
            self.theme = theme

    class Menu(Page):
        def __init__(self, master=None, theme=None, **kw):
            super().__init__(master, theme=theme)

        def create(self):
            theme = self.theme

            header = ttk.Label(self, text="PySocket")
            header.configure(style=theme.elements['h1'])

            name_entry = ttk.Frame(self, padding='20 10')
            name_entry.configure(style=theme.elements['entry'])
            name_input = EntryXL(name_entry, placeholder='named...', font=(theme.font, 16))

            name_input.configure(style=theme.elements['input'])

            host_button = ttk.Button(self, text="Host",
                                     command=lambda: start_host(name_input.get_valid_input()))
            host_button.configure(style=theme.elements['button-large'])

            join_button = ttk.Button(self, text="Join",
                                     command=lambda: start_join(name_input.get_valid_input()))
            join_button.configure(style=theme.elements['button-large'])

            self.grid()
            header.grid(column=0, row=0, pady='0 40')
            name_entry.grid(column=0, row=1, pady='0 80')
            name_input.grid(column=0, row=1)
            host_button.grid(column=0, row=2, pady='0 30')
            join_button.grid(column=0, row=3)
            self.grid_remove()

    class Host(Page):
        def __init__(self, master=None, theme=None, **kw):
            super().__init__(master, theme=theme)

        def create(self):
            theme = self.theme
            self.configure(style=theme.elements['body'])

            header = ttk.Label(self, text="PySocket")
            header.configure(style=theme.elements['h1'])

            chat_entry = ttk.Frame(self, width=50, padding=20)
            chat_entry.configure(style=theme.elements['entry'])
            chat_input = EntryXL(chat_entry, placeholder='type here...', background='#aaaaaa',
                                 font=(theme.font, 16))
            chat_input.configure(style=theme.elements['input'])

            send_button = ttk.Button(self, text="send",
                                     takefocus=False)
            send_button.configure(style=theme.elements['button'])

            chat_output = Text(self, background=theme.mg_color, foreground=theme.fg_color,
                               font=(theme.font, 16),
                               relief='flat', width=40, height=15, padx=18, pady=22)
            chat_output.bind('<FocusIn>', lambda event: self.root.chat_output.config(state='disabled'))
            self.root.focus_force()
            chat_output.bind('<FocusOut>', lambda event: self.root.chat_output.config(state='normal'))

            self.grid()
            header.grid(column=0, row=0, sticky='n')
            chat_output.grid(column=0, row=1, sticky='nswe')
            chat_entry.grid(column=0, row=2, sticky='nswe')
            chat_input.grid(column=0, row=2, sticky='nswe')
            send_button.grid(column=0, row=2, sticky='nse')
            self.grid_remove()

    class Main(Page):

        def __init__(self, master=None, theme=None, **kw):
            super().__init__(master, theme=theme)
            self.chat_output = ""
            self.input_buffer = ""
            events.register(events.Events.RECEIVE_CHAT, target=self.update_chat)
            threading.Thread()

        def update_buffer(msg):
            if msg != "":
                # gui.buffered_input = msg
                # gui.name = ""
                # gui.chat_input.delete(0, len(gui.buffered_input))
                # print(f"Buffer updated: {gui.buffered_input}")
                print(f"Sent: {msg}")

        def update_chat(self, msg):
            print(msg)
            chat.chat_input = msg
            self.chat_output.insert(0, msg)

        def create(self):
            theme = self.theme
            self.configure(style=theme.elements['body'])

            header = ttk.Label(self, text="PySocket")
            header.configure(style=theme.elements['h1'])

            chat_entry = ttk.Frame(self, width=50, padding=20)
            chat_entry.configure(style=theme.elements['entry'])
            self.chat_input = EntryXL(chat_entry, placeholder='type here...',
                                 background='#aaaaaa',
                                 font=(theme.font, 16))
            self.chat_input.configure(style=theme.elements['input'])

            send_button = ttk.Button(self, text="send",
                                     command=lambda: events.broadcast(events.Events.SEND_CHAT, chat.chat_input),
                                     takefocus=False)
            send_button.configure(style=theme.elements['button'])

            self.chat_output = Text(self, background=theme.mg_color, foreground=theme.fg_color,
                                    font=(theme.font, 16),
                                    relief='flat', width=40, height=15, padx=18, pady=22)
            self.chat_output.bind('<Button-1>', lambda: chat.set_input(self.chat_input.get()))

            self.chat_output.bind('<FocusIn>', lambda event: self.root.chat_output.config(state='disabled'))
            self.chat_output.bind('<FocusOut>', lambda event: self.root.chat_output.config(state='normal'))

            self.grid()
            header.grid(column=0, row=0, sticky='n')
            self.chat_output.grid(column=0, row=1, sticky='nswe')
            chat_entry.grid(column=0, row=2, sticky='nswe')
            self.chat_input.grid(column=0, row=2, sticky='nswe')
            send_button.grid(column=0, row=2, sticky='nse')
            self.grid_remove()

    def __init__(self, root_name='', menu=''):
        self.pages = {None: None}
        self.root_name = root_name
        self.root = Tk('modern')

        self.root.geometry("1280x720")
        theme = Modern(self.root)
        self.root.configure(background=theme.bg_color)

        style = theme.get_style()
        style.theme_use(theme.get_name())

        self.pages.clear()
        self.pages['menu'] = self.Menu(self.root, theme=theme)
        self.pages['main'] = self.Main(self.root, theme=theme)

        self.pages['menu'].create()
        self.pages['main'].create()

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        events.register(events.Events.START_CHAT, target=lambda: self.open_page(page=self.pages['main']))

        self.initialize()

    def initialize(self):
        self.open_page(page=self.pages['menu'])
        self.root.protocol('WM_DELETE_WINDOW', lambda: on_quit(self.root))
        self.root.mainloop()

    def open_page(self, page):
        for p in self.pages.values():
            p.grid_remove()

        page.grid()

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)


client_input = Input()
chat = Chat()
gui = PySocketWindow('PyChat')
