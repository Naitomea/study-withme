import time
import math
import PySimpleGUI as sg

import state
from window import Window
from enums import WindowMode
from netEnums import UserState

import timeUtils


class PromptPseudo(Window):
    def __init__(self):
        super().__init__([], "Study-withme: Connection")
        
        self._pseudo = ""

        # Events
        self.on_close = None
        self.on_submit = None

    def _initLayout(self):
        self._layout = [
            [
                sg.Text("Pseudo:"),
                sg.Input(size=(32, 1), key="_PSEUDO_", focus=True),
                sg.Button("Valid", key="_SUBMIT_")
            ],
        ]

    def open(self, title=None, modal=False):
        self._pseudo = None

        super().open(title, modal)

    def update(self, waitTime=None):
        if self._win is None or self._win.was_closed():
            return None
        
        event, values = super().update(waitTime)

        # Events Managing
        if event == sg.WIN_CLOSED:
            self._on_close()
            return False

        # Submit
        if event == "_SUBMIT_":
            self._pseudo = values["_PSEUDO_"].strip()
            self._on_submit()

        return True

    # Events
    def _on_close(self):
        self._call_event(self.on_close)
        self.close()

    def _on_submit(self):
        self._call_event(self.on_submit, self._pseudo)

    # Propeties
    @property
    def pseudo(self):
        return self._pseudo

    # Utils methods
    
