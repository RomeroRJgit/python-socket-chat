from tkinter import *
from tkinter import ttk
from tkinter.ttk import *


class Modern:
    # fields
    theme_name = 'modern'
    style = None

    # general styles
    font = 'TkDefaultFont'
    bg_color = '#3f444A'
    mg_color = '#3A3938'
    fg_color = '#C57945'
    text_color = '#454142'

    # Constant symbols
    BODY = 'body'
    H1 = 'h1'
    H2 = 'h2'
    P = 'p'
    TEXTBOX = 'textbox'
    INPUT = 'input'
    ENTRY = 'entry'
    BUTTON = 'button'
    BUTTON_LARGE = 'button-large'

    # Theme styling
    elements = {
        'body': 'TFrame',
        'h1': 'h1.TLabel',
        'h2': 'h2.TLabel',
        'p': 'p.TLabel',
        'input': 'input.TLabel',
        'entry': 'entry.TFrame',
        'textbox': '',
        'button': 'TButton',
        'button-large': 'button-large.TButton',
    }

    def __init__(self, root, style=None):
        self.style = ttk.Style(root) if style is None else style
        self.style.theme_create(self.theme_name)
        self.__configure()

    def get_name(self):
        return self.theme_name

    def get_style(self):
        return self.style

    def __configure(self):
        self.style.theme_use(self.theme_name)
        self.style.configure('TFrame', background=self.bg_color, relief='flat')

        self.style.configure('h1.TLabel', background=self.bg_color, foreground=self.fg_color, font=('Raleway', 32),
                             padding=30, relief='flat')
        self.style.configure('h2.TLabel', background=self.bg_color, foreground=self.fg_color, font=('Raleway', 24),
                             padding=30, relief='flat')
        self.style.configure('p.TLabel', background=self.bg_color, foreground=self.text_color, font=(self.font, 14),
                             relief='flat')

        self.style.configure('input.TLabel', background='#bbbbbb', foreground=self.text_color, font=(self.font, 24),
                             relief='flat')

        self.style.configure('entry.TFrame', background='#bbbbbb', foreground=self.text_color, font=(self.font, 24),
                             relief='flat')

        self.style.configure('TButton', background='#333333', foreground=self.fg_color, font=('font', 14), padding='15 10',
                             relief='flat')

        self.style.configure('button-large.TButton', background='#333333', foreground=self.fg_color, font=('font', 24),
                             padding='25 20',
                             relief='flat')

        return self.style

