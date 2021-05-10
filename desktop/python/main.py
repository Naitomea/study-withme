from enum import Enum
import os
import time
import math
import uuid
import json
import random
import PySimpleGUI as sg

from timeUtils import timeToStr


# Enum WindowMode
class WindowMode(Enum):
    NORMAL = "_NORMAL_"
    MINIMIZED = "_MINIMIZED_"
    SYSTEM_TRAY = "_SYSTEM_TRAY_"


# Global vars
pseudo = ""
stime, inWork = -1, False

# Functions
def getSyncTime(ctime):
    syncTime = 4200 - ctime % 4200
    if syncTime > 600:
        cSyncTime, inBreak = syncTime - 600, False
    else:
        cSyncTime, inBreak = 600 - syncTime, True

    return cSyncTime, inBreak

# Windows
def promptPseudo():
    sg.theme("Dark")

    layout = [
        [
            sg.Text("Pseudo:"),
            sg.Input(size=(32, 1), key="_PSEUDO_", focus=True),
            sg.Button("Valid", key="_SUBMIT_")
        ],
    ]
    window = sg.Window("WorkTimer: Connection", layout)

    pseudo = None
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            pseudo = None
            break

        if event == "_SUBMIT_":
            pseudo = values["_PSEUDO_"].strip()
            if len(pseudo) > 0:
                break

    window.close()

    return pseudo


def genUserList(idx):
    randomList = []
    for i in range(1, random.randrange(2, 11)):
        randomList.append(
            [sg.Text(f"Pseudo {i}", s=(14, None), k=f"_PSEUDO_{i}_[{idx}]")])
    return randomList


def mainWindow():
    global pseudo, stime, inWork

    # Set Theme
    sg.theme("Dark")

    # Fonts
    timeFont = ("Arial", 56)

    # Left Panel
    userIdx = 0

    userLayout = [
        [
            # [sg.Text("Naitomea", s=(15, None))],
            sg.Text(f"{pseudo}", s=(11, None)),
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
                sg.Column(genUserList(userIdx), s=(107, 172),
                          scrollable=True, vertical_scroll_only=True)
            ]
        ], k="_USER_LIST_")],
    ]

    # Time Panels
    ctime = time.time()

    # Sync.
    cSyncTime, inBreak = getSyncTime(ctime)

    syncTimeLayout = [
        [sg.Text(timeToStr(math.floor(cSyncTime), not inBreak), font=timeFont, s=(7, 1),
                 background_color="green" if inBreak else "red", justification="center",
                 k="_SYNC_TIME_")]
    ]

    # Personnal
    if stime < 0:
        personnalTimeLayout = [
            [sg.Text("00:00:00", font=timeFont, s=(7, 1),
                     background_color=sg.theme_background_color(), justification="center", k="_PERSO_TIME_")]
        ]
    else:
        elapsedTime = ctime - stime

        personnalTimeLayout = [
            [sg.Text(timeToStr(math.floor(elapsedTime), inWork), font=timeFont, s=(7, 1),
                     background_color="red" if inWork else "green", justification="center",
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
                0, 0), k="_START_BUTTONS_", visible=stime < 0),
            sg.Column(breakButtonsLayout, s=(332, 32), pad=(
                0, 0), k="_BREAK_BUTTONS_", visible=not stime < 0 and inWork),
            sg.Column(resumeButtonsLayout, s=(332, 32), pad=(
                0, 0), k="_RESUME_BUTTONS_", visible=not stime < 0 and not inWork),
        ],
        [sg.Frame("Personnal Time:", personnalTimeLayout, pad=(5, (12, 3)))]
    ]

    # Main Layout
    layout = [
        [
            sg.Column(leftPanelLayout, s=(150, 300)),
            sg.Column(timePanelsLayout, s=(340, 300)),
        ],
    ]

    # Main Window
    win = sg.Window("WorkTimer", layout)

    # Main Loop
    retVal = None
    while True:
        event, values = win.read(500)

        # Events Managing
        if event == sg.WIN_CLOSED:
            break

        # Minimized
        elif event == "_MINIMIZED_MODE_":
            retVal = WindowMode.MINIMIZED
            break

        # Start/Resume Button
        if event == "_START_" or event == "_RESUME_":
            inWork, stime = True, time.time()

            # Destroy UserList
            win["_USER_LIST_"].Widget.children[
                list(win["_USER_LIST_"].Widget.children.keys())[0]
            ].destroy()

            # Gen new UserList
            userIdx += 1
            userList = genUserList(userIdx)
            win.extend_layout(win["_USER_LIST_"], [
                [
                    sg.Column(userList, s=(107, 172),
                              scrollable=True, vertical_scroll_only=True)
                ]
            ])

        # Break Button
        elif event == "_BREAK_":
            inWork, stime = False, time.time()
        # Stop Button
        elif event == "_STOP_BREAK_" or event == "_STOP_RESUME_":
            stime = -1

        # Update Times
        ctime = time.time()

        # Sync. time
        syncTime = 4200 - ctime % 4200
        if syncTime > 600:
            cSyncTime, inBreak = syncTime - 600, False
        else:
            cSyncTime, inBreak = 600 - syncTime, True

        win["_SYNC_TIME_"].update(value=timeToStr(math.floor(cSyncTime), not inBreak),
                                  background_color="green" if inBreak else "red")

        # Personnal Time
        if stime < 0:
            win["_PERSO_TIME_"].update(value="00:00:00",
                                       background_color=win.BackgroundColor)
        else:
            elapsedTime = ctime - stime
            win["_PERSO_TIME_"].update(value=timeToStr(math.floor(elapsedTime), inWork),
                                       background_color="red" if inWork else "green")

        # Buttons
        win["_START_BUTTONS_"].update(visible=stime < 0)
        win["_BREAK_BUTTONS_"].update(visible=not stime < 0 and inWork)
        win["_RESUME_BUTTONS_"].update(visible=not stime < 0 and not inWork)

    win.close()

    return retVal


def minimizedWindow():
    global pseudo, stime, inWork

    # Set Theme
    sg.theme("Dark")

    # Fonts
    font = ("Arial", 8)

    # Times
    ctime = time.time()

    # Sync.
    cSyncTime, inBreak = getSyncTime(ctime)

    syncTimeEl = sg.Text(timeToStr(math.floor(cSyncTime), not inBreak), s=(7, 1),
                         background_color="green" if inBreak else "red", justification="center",
                         k="_SYNC_TIME_")

    # Personnal
    if stime < 0:
        personnalTimeEl = sg.Text("00:00:00", s=(7, 1),
                                  background_color=sg.theme_background_color(), justification="center",
                                  k="_PERSO_TIME_")
    else:
        elapsedTime = ctime - stime

        personnalTimeEl = sg.Text(timeToStr(math.floor(elapsedTime), inWork), s=(7, 1),
                                  background_color="red" if inWork else "green", justification="center",
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
    layout = [
        [
            sg.Button("+", button_color=(sg.theme_text_color(), sg.theme_background_color()), border_width=0,
                      # sg.Button("+", button_color=(sg.theme_text_color(), sg.theme_background_color()),
                      s=(2, 1), k="_NORMAL_MODE_"),

            # Time Panels
            syncTimeEl,
            personnalTimeEl,

            sg.VerticalSeparator(),

            # Time Buttons
            sg.Column(startButtonsLayout, pad=(0, 0),
                      k="_START_BUTTONS_", visible=stime < 0),
            sg.Column(breakButtonsLayout, pad=(0, 0),
                      k="_BREAK_BUTTONS_", visible=not stime < 0 and inWork),
            sg.Column(resumeButtonsLayout, pad=(0, 0),
                      k="_RESUME_BUTTONS_", visible=not stime < 0 and not inWork),
        ],
    ]

    # Main Window
    win = sg.Window("WorkTimer", layout, font=font, margins=(0, 0),
                    no_titlebar=True, grab_anywhere=True, keep_on_top=True)

    # Main Loop
    retVal = None
    while True:
        event, values = win.read(500)

        # Events Managing
        if event == sg.WIN_CLOSED:
            break

        # Maximized
        elif event == "_NORMAL_MODE_":
            retVal = WindowMode.NORMAL
            break

        # Start/Resume Button
        if event == "_START_" or event == "_RESUME_":
            inWork, stime = True, time.time()

        # Break Button
        elif event == "_BREAK_":
            inWork, stime = False, time.time()
        # Stop Button
        elif event == "_STOP_BREAK_" or event == "_STOP_RESUME_":
            stime = -1

        # Update Times
        ctime = time.time()

        # Sync. time
        syncTime = 4200 - ctime % 4200
        if syncTime > 600:
            cSyncTime, inBreak = syncTime - 600, False
        else:
            cSyncTime, inBreak = 600 - syncTime, True

        win["_SYNC_TIME_"].update(value=timeToStr(math.floor(cSyncTime), not inBreak),
                                  background_color="green" if inBreak else "red")

        # Personnal Time
        if stime < 0:
            win["_PERSO_TIME_"].update(value="00:00:00",
                                       background_color=win.BackgroundColor)
        else:
            elapsedTime = ctime - stime
            win["_PERSO_TIME_"].update(value=timeToStr(math.floor(elapsedTime), inWork),
                                       background_color="red" if inWork else "green")

        # Buttons
        win["_START_BUTTONS_"].update(visible=stime < 0)
        win["_BREAK_BUTTONS_"].update(visible=not stime < 0 and inWork)
        win["_RESUME_BUTTONS_"].update(visible=not stime < 0 and not inWork)

    win.close()

    return retVal

# Main entry
def main():
    global pseudo

    # Get Pseudo
    # pseudo = promptPseudo()
    # if pseudo is None:
    #     return
    pseudo = "Naitomea"

    # Launch windows loop (main loop)
    currentMode = WindowMode.NORMAL
    while 42:
        if currentMode == WindowMode.NORMAL:
            currentMode = mainWindow()
        elif currentMode == WindowMode.MINIMIZED:
            currentMode = minimizedWindow()

        if currentMode is None:
            break


# Start
if __name__ == '__main__':
    main()
