import logging
import socket
import sys
import threading
import select
from tkinter import *
from tkinter import messagebox
from tkinter import ttk
from time import sleep
from themes import Modern


class Server:
    active_conns = []
    connections = {None: None}

    host = '127.0.0.1'
    port = 8080

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
                    logging.warning("SIGEND: closing server")
                    return SIGEND

                for r in receivable:
                    if r == sock:
                        conn, addr = sock.accept()
                        print(conn)
                        self.active_conns.append(conn)

                        print(f"conn: {conn}")

                        conn_thread = threading.Thread(target=self.listen, args=(conn,))
                        conn_thread.start()

    def listen(self, conn):
        conn.sendall(f"[Server] Welcome to PyChat! ({len(self.active_conns)})".encode())
        conn.setblocking(TRUE)
        initialized = ""

        while True:
            data = conn.recv(1024)

            if (not initialized) and int(data.decode()[0]) == int(SIGJOIN):
                print(f"SIGJOIN: {data.decode()[1:]}")
                self.connections[conn] = data.decode()[1:]
                initialized = TRUE
                continue

            if not data:
                logging.warning("Client disconnected...")

            if end_signal.is_set() or data == SIGEND:
                logging.warning("SIGEND: Closing server")
                return SIGEND

            if not initialized:
                continue

            for c in self.active_conns:
                c.sendall(f"[{self.connections[conn]}] ".encode() + data)


class Client:
    host = '127.0.0.1'
    port = 8080

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def launch(self, name):
        global buffered_input
        global chat_output

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.host, self.port))
            sock.sendall(SIGJOIN + name.encode())
            print(f"SIGJOIN + {name.encode()}")

            sock.setblocking(FALSE)

            read_socket_list = [sock]
            write_socket_list = [sock]

            while True:
                receivable, writeable, err = select.select(read_socket_list, write_socket_list, [], 1)

                if end_signal.is_set():
                    sock.sendall(SIGEND)
                    logging.warning("closing client")
                    sleep(1)
                    return

                for r in receivable:
                    if r == sock:
                        data = sock.recv(1024)

                        if not data:
                            break

                        chat_output.insert('end', data.decode() + "\n")
                        print(data)

                for w in writeable:
                    if w == sock:
                        if buffered_input != "":
                            sock.sendall(buffered_input.encode())
                            buffered_input = ""


host = '127.0.0.1'
port = 8080
name = "default"

buffered_input = ""
chat_input = None
chat_output = None

end_signal = threading.Event()

HOST = b'0'
CLIENT = b'1'
SIGJOIN = b'8'
SIGEND = b'-1'

server = Server(host, port)
client = Client(host, port)

main_thread = threading.current_thread()
server_thread = threading.Thread(target=server.launch)
client_thread = None


def switch_grids(root, current_frame, next_frame):
    current_frame.grid_forget()
    next_frame.grid()

    root.columnconfigure(next_frame, weight=1)
    root.rowconfigure(next_frame, weight=1)


def start_host(name):
    global client_thread
    client_thread = threading.Thread(target=client.launch, args=(name,))

    switch_grids(root, menu, content)

    server_thread.start()

    sleep(1)

    client_thread.start()


def start_join(name):
    global client_thread
    client_thread = threading.Thread(target=client.launch, args=(name,))

    switch_grids(root, menu, content)
    client_thread.start()


def on_quit():
    global end_signal
    confirmation = messagebox.askyesno("Quit?", "Do you want to end the connection and quit?")

    if confirmation:
        end_signal = threading.Event()
        end_signal.set()
        if client_thread.is_alive():
            client_thread.join(3)
            logging.warning('client thread joined')
        if server_thread.is_alive():
            server_thread.join(3)
            if server_thread.is_alive():
                # sys.exit(server_thread)
                logging.warning('server thread forcibly terminated')
            else:
                logging.warning('server thread joined')
        root.destroy()


def update_buffer(msg):
    global chat_input
    global buffered_input
    buffered_input = msg
    chat_input.delete(0, len(buffered_input))
    print(f"Buffer updated: {buffered_input}")


# region Window Setup
root = Tk('modern')
root.geometry("1280x720")
theme = Modern(root)
root.configure(background=theme.bg_color)

style = theme.get_style()
style.theme_use(theme.get_name())
# endregion

# region Menu Setup (Page 1)
menu = ttk.Frame(root)
menu.configure(style=theme.elements['body'])

header = ttk.Label(menu, text="PySocket")
header.configure(style=theme.elements['h1'])

name_entry = ttk.Frame(menu, width=50, padding=20)
name_entry.configure(style=theme.elements['entry'])
name_input = ttk.Entry(name_entry, background='#aaaaaa', font=(theme.font, 16))
name_input.configure(style=theme.elements['input'])

host_button = ttk.Button(menu, text="Host", command=lambda: start_host(name_input.get()))
host_button.configure(style=theme.elements['button-large'])

join_button = ttk.Button(menu, text="Join", command=lambda: start_join(name_input.get()))
join_button.configure(style=theme.elements['button-large'])

menu.grid()
root.columnconfigure(menu, weight=1)
root.rowconfigure(menu, weight=1)
menu.grid(column=0, row=0)
header.grid(column=0, row=0, pady='0 20')
name_entry.grid(column=0, row=1, sticky='nswe', pady='0 80')
name_input.grid(column=0, row=1, sticky='nswe')
host_button.grid(column=0, row=2, pady='0 30')
join_button.grid(column=0, row=3, pady='0 30')
# endregion

# region Content Setup (Page 2)
content = ttk.Frame(root)
content.configure(style=theme.elements['body'])

header = ttk.Label(content, text="PySocket")
header.configure(style=theme.elements['h1'])

chat_entry = ttk.Frame(content, width=50, padding=20)
chat_entry.configure(style=theme.elements['entry'])
chat_input = ttk.Entry(chat_entry, background='#aaaaaa', font=(theme.font, 16))
chat_input.configure(style=theme.elements['input'])

send_button = ttk.Button(content, text="send", command=lambda: update_buffer(chat_input.get()))
send_button.configure(style=theme.elements['button'])

chat_output = Text(content, background=theme.mg_color, foreground=theme.fg_color, font=(theme.font, 16),
                   relief='flat', width=40, height=15, padx=18, pady=22)

header.grid(column=0, row=0, sticky='n')
chat_output.grid(column=0, row=1, sticky='nswe')
chat_entry.grid(column=0, row=2, sticky='nswe')
chat_input.grid(column=0, row=2, sticky='nswe')
send_button.grid(column=0, row=2, sticky='nse')
# endregion

# ------------

root.protocol('WM_DELETE_WINDOW', on_quit)

root.mainloop()
