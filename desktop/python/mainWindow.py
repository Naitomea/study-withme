import time
import math
import PySimpleGUI as sg

import state
from window import Window
from enums import WindowMode
from netEnums import UserState

import timeUtils


class MainWindow(Window):
    def __init__(self):
        super().__init__([], "Study-withme")

        self._statusText = ""
        self._userIdx = 0

        # Events
        self.on_close = None
        self.on_minimize = None

        self.on_start = None
        self.on_break = None
        self.on_stop = None

        self.on_rename = None
        self.on_history = None
        self.on_parameters = None

    def _initLayout(self):
        # Set Theme
        sg.theme("Dark")

        # Fonts
        timeFont = ("Arial", 56)

        # Left Panel
        userLayout = [
            [
                # [sg.Text("Naitomea", s=(15, None))],
                sg.Text(f"{state.pseudo}", s=(11, None), k="_PSEUDO_"),
                # sg.Text("", s=(11, None), k="_PSEUDO_"),
                # sg.Button("-", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0,
                sg.Button("-", button_color=(sg.theme_text_color(), sg.theme_background_color()),
                          s=(2, 1), k="_MINIMIZED_MODE_"),
            ],
            [
                sg.ButtonMenu("Settings",
                              ['Unused', ["&Change pseudo", "&History", "&Parameters"]],
                              button_color="grey", s=(16, 1))
            ]
        ]

        leftPanelLayout = [
            [sg.Frame("User:", userLayout)],
            [sg.Frame("Connected Users:", [
                [
                    # sg.Column([], s=(107, 172),
                    sg.Column(self._genUserList(), s=(107, 172),
                              scrollable=True, vertical_scroll_only=True)
                ]
            ], k="_USER_LIST_")],
        ]

        # Time Panels
        ctime = time.time()

        # Sync.
        cSyncTime, inBreak = timeUtils.getSyncTime(ctime)

        syncTimeLayout = [
            [sg.Text(timeUtils.timeToStr(math.floor(cSyncTime), not inBreak), font=timeFont, s=(7, 1),
                     background_color="green" if inBreak else "red", justification="center",
                     k="_SYNC_TIME_")]
        ]

        # Personnal
        if state.stime < 0:
            personnalTimeLayout = [
                [sg.Text("00:00:00", font=timeFont, s=(7, 1),
                         background_color=sg.theme_background_color(), justification="center", k="_PERSO_TIME_")]
            ]
        else:
            elapsedTime = ctime - state.stime

            personnalTimeLayout = [
                [sg.Text(timeUtils.timeToStr(math.floor(elapsedTime), state.inWork), font=timeFont, s=(7, 1),
                         background_color="red" if state.inWork else "green", justification="center",
                         k="_PERSO_TIME_")]
            ]

        # Buttons layouts
        startButtonsLayout = [
            [
                sg.Button("Let's work!", button_color=("white", "blue"), s=(39, 1),
                          focus=True, k="_START_")
            ]
        ]

        breakButtonsLayout = [
            [
                sg.Button("I'm done", button_color=("black", "red"), s=(10, 1),
                          k="_STOP_BREAK_"),
                sg.Button("Time to take break :)", button_color="green", s=(27, 1),
                          focus=True, k="_BREAK_"),
            ]
        ]

        resumeButtonsLayout = [
            [
                sg.Button("I'm done", button_color=("black", "red"), s=(10, 1),
                          k="_STOP_RESUME_"),
                sg.Button("Get back to work!", button_color=("white", "blue"), s=(27, 1),
                          focus=True, k="_RESUME_"),
            ]
        ]

        timePanelsLayout = [
            [sg.Frame("Sync. Time:", syncTimeLayout, pad=(5, (3, 12)))],
            [
                sg.Column(startButtonsLayout, s=(332, 32), pad=(
                    0, 0), k="_START_BUTTONS_", visible=state.stime < 0),
                sg.Column(breakButtonsLayout, s=(332, 32), pad=(
                    0, 0), k="_BREAK_BUTTONS_", visible=not state.stime < 0 and state.inWork),
                sg.Column(resumeButtonsLayout, s=(332, 32), pad=(
                    0, 0), k="_RESUME_BUTTONS_", visible=not state.stime < 0 and not state.inWork),
            ],
            [sg.Frame("Personnal Time:", personnalTimeLayout, pad=(5, (12, 3)))]
        ]

        # Main Layout
        self._layout = [
            [
                sg.Column(leftPanelLayout, s=(150, 300)),
                sg.Column(timePanelsLayout, s=(340, 300)),
            ],
            [
                sg.StatusBar(self._statusText, s=(62, None), k="_STATUS_")
            ]
        ]

    def open(self, statusText=None):
        if not statusText == None:
            self.updateStatus(statusText)

        super().open()

    def update(self, waitTime=None):
        if self._win is None or self._win.was_closed():
            return None

        event, values = super().update(waitTime)

        # Events Managing
        if event == sg.WIN_CLOSED:
            self._on_close()
            return False

        # Minimized
        elif event == "_MINIMIZED_MODE_":
            self._on_minimize()
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

    def _on_minimize(self):
        self._call_event(self.on_minimize)
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
    def updateStatus(self, text):
        self._statusText = text

        if not self.isOpen():
            return

        self["_STATUS_"].update(value=self._statusText)

    def updateUserList(self):
        if not self.isOpen():
            return

        # Destroy UserList
        self["_USER_LIST_"].Widget.children[
            list(self["_USER_LIST_"].Widget.children.keys())[0]
        ].destroy()

        # Create it!
        self._win.extend_layout(self["_USER_LIST_"], [
            [
                sg.Column(self._genUserList(), s=(107, 172),
                          scrollable=True, vertical_scroll_only=True)
            ]
        ])

    def updateUserState(self, pseudo, state):
        if not self.isOpen():
            return

        self[f"_{pseudo.lower()}_[{self._userIdx}]"].update(
            background_color=self._getUserStateColor(state))

    def updatePseudo(self, pseudo):
        if self.isOpen():
            self["_PSEUDO_"].update(value=pseudo)

    def _genUserList(self):
        self._userIdx += 1

        return [
            [
                sg.Text(user["pseudo"], s=(14, None),
                        k=f"_{user['pseudo'].lower()}_[{self._userIdx}]",
                        background_color=self._getUserStateColor(user["state"])
                        )
            ]
            for user in state.userList]

    def _getUserStateColor(self, userState):
        return sg.theme_background_color() if userState == UserState.REST else (
            "green" if userState == UserState.BREAK else "red")

    def clearUserList(self, keepUser=True):
        if keepUser:
            state.userList = [user for user in state.userList if user["pseudo"].lower()
                        == state.pseudo.lower()]
        else:
            state.userList = []

        self.updateUserList()
