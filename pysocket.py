import socket
from tkinter import *
from tkinter import ttk
from themes import Modern

# region Window Setup
root = Tk('modern')
root.geometry("1280x720")
theme = Modern(root)
root.configure(background=theme.bg_color)

style = theme.get_style()
style.theme_use(theme.get_name())
# endregion

# region Widget Setup
content = ttk.Frame(root)
content.configure(style=theme.elements['body'])

header = ttk.Label(content, text="PySocket")
header.configure(style=theme.elements['h1'])

chat_entry = ttk.Frame(content, width=50, padding=20)
chat_entry.configure(style=theme.elements['entry'])
chat_input = ttk.Entry(chat_entry, background='#aaaaaa', font=(theme.font, 16))
chat_input.configure(style=theme.elements['input'])

send_button = ttk.Button(content, text="send", command=None)
send_button.configure(style=theme.elements['button'])

# send_btn = ttk.Button(content, text='Send', command=None)

chat_box = Text(content, background=theme.mg_color, foreground=theme.fg_color, font=(theme.font, 16),
                relief='flat', width=40, height=15, padx=18, pady=22)
# endregion


# region Grid Setup
content.grid()
root.columnconfigure(content, weight=1)
root.rowconfigure(content, weight=1)
header.grid(column=0, row=0, sticky='n')
chat_box.grid(column=0, row=1, sticky='nswe')
chat_entry.grid(column=0, row=2, sticky='nswe')
chat_input.grid(column=0, row=0, sticky='nswe')
send_button.grid(column=0, row=2, sticky='nse')
#send_btn.grid(column=0, row=2, sticky='nse')

# endregion

# ------------

root.mainloop()
