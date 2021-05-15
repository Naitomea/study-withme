from enum import Enum, IntEnum
import os
import time
import math
import uuid
import json
import random
import PySimpleGUI as sg
import asyncio
import websockets
import queue

from timeUtils import timeToStr

# Enum WindowMode


class WindowMode(Enum):
    NORMAL = "_NORMAL_"
    MINIMIZED = "_MINIMIZED_"
    SYSTEM_TRAY = "_SYSTEM_TRAY_"

# Enum Net


class MessageCode(IntEnum):
    ADMIN = 0
    MESSAGE = 1
    ACTION = 2
    USERS = 3
    LOGIN = 5
    LOGOUT = 6
    SIGNUP = 7


class ActionType(IntEnum):
    START = 0
    BREAK = 1
    STOP = 2


class UserState(IntEnum):
    REST = 0
    WORK = 1
    BREAK = 2


# Global vars
asyncLoop = None
running = True

win = None
winMode = WindowMode.NORMAL

# State
pseudo = None
stime, inWork = -1, False

userList = []
userIdx = 0

# Net
msgQueue = queue.Queue()

# Net state
pseudoAccepted = False

#############
# Functions #
#############


def getSyncTime(ctime):
    syncTime = 4200 - ctime % 4200
    if syncTime > 600:
        cSyncTime, inBreak = syncTime - 600, False
    else:
        cSyncTime, inBreak = 600 - syncTime, True

    return cSyncTime, inBreak

######
# UI #
######


async def promptPseudo():
    global pseudo

    sg.theme("Dark")

    layout = [
        [
            sg.Text("Pseudo:"),
            sg.Input(size=(32, 1), key="_PSEUDO_", focus=True),
            sg.Button("Valid", key="_SUBMIT_")
        ],
    ]

    window = sg.Window("Study-withme: Connection", layout)

    pseudo = None
    while True:
        if pseudoAccepted:
            break

        event, values = window.read(100)
        if event == sg.WIN_CLOSED:
            pseudo = None
            break

        if event == "_SUBMIT_":
            pseudo = values["_PSEUDO_"].strip()
            if len(pseudo) > 0:
                send(MessageCode.LOGIN, pseudo)

        # Pause
        await asyncio.sleep(0)

    window.close()


def getUserStateColor(userState):
    return sg.theme_background_color() if userState == UserState.REST else (
        "green" if userState == UserState.BREAK else "red")


def hasUserList():
    return not win.was_closed() and winMode == WindowMode.NORMAL


def genRandomUserList(idx):
    randomList = []
    for i in range(1, random.randrange(2, 11)):
        randomList.append(
            [sg.Text(f"Pseudo {i}", s=(14, None), k=f"_PSEUDO_{i}_[{idx}]")])
    return randomList


def genUserList():
    global userIdx

    userIdx += 1
    return [
        [
            sg.Text(user["pseudo"], s=(14, None),
                    k=f"_{user['pseudo'].lower()}_[{userIdx}]",
                    background_color=getUserStateColor(user["state"])
                    )
        ]
        for user in userList]


def updateUserList():
    if not hasUserList():
        return

    # Destroy UserList
    win["_USER_LIST_"].Widget.children[
        list(win["_USER_LIST_"].Widget.children.keys())[0]
    ].destroy()

    # Create it!
    win.extend_layout(win["_USER_LIST_"], [
        [
            sg.Column(genUserList(), s=(107, 172),
                      scrollable=True, vertical_scroll_only=True)
        ]
    ])


async def mainWindow():
    global stime, inWork, win, winMode

    # Set Theme
    sg.theme("Dark")

    # Fonts
    timeFont = ("Arial", 56)

    # Left Panel
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
                # sg.Column([], s=(107, 172),
                sg.Column(genUserList(), s=(107, 172),
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
    win = sg.Window("Study-withme", layout)

    # Main Loop
    while True:
        event, values = win.read(100)

        # Events Managing
        if event == sg.WIN_CLOSED:
            winMode = None
            break

        # Minimized
        elif event == "_MINIMIZED_MODE_":
            winMode = WindowMode.MINIMIZED
            break

        # Start/Resume Button
        if event == "_START_" or event == "_RESUME_":
            inWork, stime = True, time.time()
            send(MessageCode.ACTION, ActionType.START)

        # Break Button
        elif event == "_BREAK_":
            inWork, stime = False, time.time()
            send(MessageCode.ACTION, ActionType.BREAK)

        # Stop Button
        elif event == "_STOP_BREAK_" or event == "_STOP_RESUME_":
            stime = -1
            send(MessageCode.ACTION, ActionType.STOP)

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

        # Pause
        await asyncio.sleep(0)

    win.close()


async def minimizedWindow():
    global stime, inWork, win, winMode

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
    win = sg.Window("Study-withme", layout, font=font, margins=(0, 0),
                    no_titlebar=True, grab_anywhere=True, keep_on_top=True)

    # Main Loop
    while True:
        event, values = win.read(100)

        # Events Managing
        if event == sg.WIN_CLOSED:
            winMode = None
            break

        # Maximized
        elif event == "_NORMAL_MODE_":
            winMode = WindowMode.NORMAL
            break

        # Start/Resume Button
        if event == "_START_" or event == "_RESUME_":
            inWork, stime = True, time.time()
            send(MessageCode.ACTION, ActionType.START)

        # Break Button
        elif event == "_BREAK_":
            inWork, stime = False, time.time()
            send(MessageCode.ACTION, ActionType.BREAK)

        # Stop Button
        elif event == "_STOP_BREAK_" or event == "_STOP_RESUME_":
            stime = -1
            send(MessageCode.ACTION, ActionType.STOP)

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

        # Pause
        await asyncio.sleep(0)

    win.close()


async def ui():
    global winMode, running

    # Get Pseudo
    await promptPseudo()
    if not pseudo is None:
        # Launch windows loop (main loop)
        winMode = WindowMode.NORMAL
        while 42:
            if winMode == WindowMode.NORMAL:
                await mainWindow()
            elif winMode == WindowMode.MINIMIZED:
                await minimizedWindow()

            if winMode is None:
                break

    running = False

###########
# Network #
###########


def getUserId(pseudo):
    return [i for i, v in enumerate(userList)
            if v["pseudo"].lower() == pseudo.lower()][0]


def send(code, data):
    msgQueue.put_nowait({
        "code": code,
        "data": data
    })


async def producer():
    while running:
        if msgQueue.empty():
            await asyncio.sleep(0)
        else:
            return msgQueue.get_nowait()


async def producer_handler(ws):
    while running:
        message = await producer()
        if not message == None:
            print(f"[{timeToStr(time.time())}][NET SEND] {message}")
            await ws.send(json.dumps(message))


def on_login(data):
    global pseudoAccepted, userList

    if isinstance(data, bool):
        pseudoAccepted = data
    elif isinstance(data, str):
        userList.append({
            "pseudo": data,
            "state": UserState.REST
        })

        updateUserList()


def on_logout(data):
    global userList

    del userList[getUserId(data)]

    updateUserList()


def on_users(data):
    global userList

    userList = data

    updateUserList()


def on_action(data):
    global userList

    if "action" in data and "pseudo" in data:
        userState = UserState.WORK if data["action"] == ActionType.START else (
            UserState.BREAK if data["action"] == ActionType.BREAK else UserState.REST)

        userList[getUserId(data["pseudo"])]["state"] = userState

        if hasUserList():
            win[f"_{data['pseudo'].lower()}_[{userIdx}]"].update(
                background_color=getUserStateColor(userState))


async def consumer(message):
    message = json.loads(message)
    print(f"[{timeToStr(time.time())}][NET RECV] {message}")

    if "code" in message:
        if message["code"] == MessageCode.ADMIN:
            42
        elif message["code"] == MessageCode.MESSAGE:
            42
        elif message["code"] == MessageCode.ACTION:
            on_action(message["data"])
        elif message["code"] == MessageCode.USERS:
            on_users(message["data"])
        elif message["code"] == MessageCode.LOGIN:
            on_login(message["data"])
        elif message["code"] == MessageCode.LOGOUT:
            on_logout(message["data"])
        elif message["code"] == MessageCode.SIGNUP:
            42
        else:
            42

    await asyncio.sleep(0)


async def consumer_handler(ws):
    async for message in ws:
        await consumer(message)


async def handler(ws):
    consumer_task = asyncio.ensure_future(
        consumer_handler(ws))
    producer_task = asyncio.ensure_future(
        producer_handler(ws))
    done, pending = await asyncio.wait(
        [consumer_task, producer_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()


async def net():
    # uri = "ws://localhost:31492"
    uri = "ws://study-withme.herokuapp.com"
    async with websockets.connect(uri) as ws:
        await handler(ws)

##############
# Main entry #
##############


async def wait_list():
    await asyncio.wait([
        asyncio.create_task(net()),
        asyncio.create_task(ui())
    ])


def main():
    global asyncLoop

    asyncLoop = asyncio.get_event_loop()
    asyncLoop.run_until_complete(wait_list())


# Start
if __name__ == '__main__':
    main()
