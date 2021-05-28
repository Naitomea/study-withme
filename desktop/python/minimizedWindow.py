import time
import math
import PySimpleGUI as sg

import state
from window import Window
from enums import WindowMode
from netEnums import UserState

import timeUtils


class MinimizedWindow(Window):
    def __init__(self):
        super().__init__([], "Study-withme")

        self._statusText = ""
        self._userIdx = 0

        # Events
        self.on_close = None
        self.on_maximize = None

        self.on_start = None
        self.on_break = None
        self.on_stop = None

    def _initLayout(self):
        # Times
        ctime = time.time()
        
        # Sync.
        cSyncTime, inBreak = timeUtils.getSyncTime(ctime)

        syncTimeEl = sg.Text(timeUtils.timeToStr(math.floor(cSyncTime), not inBreak), s=(7, 1),
                             background_color="green" if inBreak else "red", justification="center",
                             k="_SYNC_TIME_")

        # Personnal
        if state.stime < 0:
            personnalTimeEl = sg.Text("00:00:00", s=(7, 1),
                                      background_color=sg.theme_background_color(), justification="center",
                                      k="_PERSO_TIME_")
        else:
            elapsedTime = ctime - state.stime

            personnalTimeEl = sg.Text(timeUtils.timeToStr(math.floor(elapsedTime), state.inWork), s=(7, 1),
                                      background_color="red" if state.inWork else "green", justification="center",
                                      k="_PERSO_TIME_")

        # Buttons layouts
        startButtonsLayout = [
            [
                sg.Button("Work!", button_color=("white", "blue"),
                          s=(20, 1), focus=True, k="_START_")
            ]
        ]

        breakButtonsLayout = [
            [
                sg.Button("Done", button_color=("black", "red"),
                          s=(5, 1), k="_STOP_BREAK_"),
                sg.Button("Break!", button_color="green",
                          s=(12, 1), focus=True, k="_BREAK_"),
            ]
        ]

        resumeButtonsLayout = [
            [
                sg.Button("Done", button_color=("black", "red"),
                          s=(5, 1), k="_STOP_RESUME_"),
                sg.Button("Work!", button_color=("white", "blue"),
                          s=(12, 1), focus=True, k="_RESUME_"),
            ]
        ]

        # Main Layout
        self._layout = [
            [
                # sg.Button("+", button_color=(sg.theme_text_color(), sg.theme_background_color()),
                sg.Button("+", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0,
                          s=(2, 1), k="_NORMAL_MODE_"),

                # Time Panels
                syncTimeEl,
                personnalTimeEl,

                sg.VerticalSeparator(),

                # Time Buttons
                sg.Column(startButtonsLayout, pad=(0, 0),
                          k="_START_BUTTONS_", visible=state.stime < 0),
                sg.Column(breakButtonsLayout, pad=(0, 0),
                          k="_BREAK_BUTTONS_", visible=not state.stime < 0 and state.inWork),
                sg.Column(resumeButtonsLayout, pad=(0, 0),
                          k="_RESUME_BUTTONS_", visible=not state.stime < 0 and not state.inWork),
            ],
        ]

    def open(self):
        self._initLayout()
        self._win = sg.Window(self._title, self._layout,
                              no_titlebar=True, grab_anywhere=True, keep_on_top=True,
                              margins=(0, 0), font=("Arial", 8))

    def update(self, waitTime=None):
        if self._win is None or self._win.was_closed():
            return None

        event, values = super().update(waitTime)

        # Events Managing
        if event == sg.WIN_CLOSED:
            self._on_close()
            return False

        # Minimized
        elif event == "_NORMAL_MODE_":
            self._on_maximize()
            return True

        # Start/Resume Button
        if event == "_START_" or event == "_RESUME_":
            self._on_start()

        # Break Button
        elif event == "_BREAK_":
            self._on_break()

        # Stop Button
        elif event == "_STOP_BREAK_" or event == "_STOP_RESUME_":
            self._on_stop()

        # Update Times
        ctime = time.time()

        # Sync. time
        cSyncTime, inBreak = timeUtils.getSyncTime(ctime)

        self["_SYNC_TIME_"].update(value=timeUtils.timeToStr(math.floor(cSyncTime), not inBreak),
                                   background_color="green" if inBreak else "red")

        # Personnal Time
        if state.stime < 0:
            self["_PERSO_TIME_"].update(value="00:00:00",
                                        background_color=self._win.BackgroundColor)
        else:
            elapsedTime = ctime - state.stime
            self["_PERSO_TIME_"].update(value=timeUtils.timeToStr(math.floor(elapsedTime), state.inWork),
                                        background_color="red" if state.inWork else "green")

        # Buttons
        self["_START_BUTTONS_"].update(visible=state.stime < 0)
        self["_BREAK_BUTTONS_"].update(
            visible=not state.stime < 0 and state.inWork)
        self["_RESUME_BUTTONS_"].update(
            visible=not state.stime < 0 and not state.inWork)

        return True

    # Events
    def _on_close(self):
        self._call_event(self.on_close)
        self.close()

    def _on_maximize(self):
        self._call_event(self.on_maximize)
        self.close()

    def _on_start(self):
        state.inWork, state.stime = True, time.time()

        self._call_event(self.on_start)

    def _on_break(self):
        state.inWork, state.stime = False, time.time()

        self._call_event(self.on_break)

    def _on_stop(self):
        state.stime = -1

        self._call_event(self.on_stop)

    # Utils methods
