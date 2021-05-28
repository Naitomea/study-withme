from enum import Enum, IntEnum
import os
import time
import math
from typing import final
import uuid
import json
import random
import PySimpleGUI as sg
import asyncio
import websockets
import socket
import queue
import sys

from timeUtils import timeToStr

from enums import WindowMode
from netEnums import MessageCode, ActionType, UserState

from mainWindow import MainWindow
from minimizedWindow import MinimizedWindow
from promptPseudo import PromptPseudo

import state
import netState

sg.theme("Dark")

# Global vars
asyncLoop = None
running = True

winNormal = None
winMinimized = None

promptPseudo = None

# Net
connected = False
reconnectingAttempts = 0

msgQueue = queue.Queue()
msgLogin = None

#############
# Functions #
#############

######
# UI #
######
# def genRandomUserList(idx):
#     randomList = []
#     for i in range(1, random.randrange(2, 11)):
#         randomList.append(
#             [sg.Text(f"Pseudo {i}", s=(14, None), k=f"_PSEUDO_{i}_[{idx}]")])
#     return randomList


def on_close():
    global running

    running = False


def on_minimize():
    winMinimized.open()


def on_maximize():
    winNormal.open()


def on_start():
    send(MessageCode.ACTION, ActionType.START)


def on_break():
    send(MessageCode.ACTION, ActionType.BREAK)


def on_stop():
    send(MessageCode.ACTION, ActionType.STOP)


def on_submit_pseudo(pseudo):
    if len(pseudo) > 0:
        send(MessageCode.LOGIN, pseudo)


async def ui():
    global running, \
        winNormal, winMinimized, \
        promptPseudo

    winNormal = MainWindow()
    # winNormal.on_close = on_close
    winNormal.on_minimize = on_minimize
    winNormal.on_start = on_start
    winNormal.on_break = on_break
    winNormal.on_stop = on_stop

    winMinimized = MinimizedWindow()
    # winMinimized.on_close = on_close
    winMinimized.on_maximize = on_maximize
    winMinimized.on_start = on_start
    winMinimized.on_break = on_break
    winMinimized.on_stop = on_stop

    promptPseudo = PromptPseudo()
    # promptPseudo.on_close = on_close
    promptPseudo.on_submit = on_submit_pseudo

    promptPseudo.open()
    while running:
        if promptPseudo.isOpen():
            if promptPseudo.update(100) == False and netState.pseudoAccepted == False:
                break

        if winNormal.isOpen() and winNormal.update(100) == False:
            break
        elif winMinimized.isOpen() and winMinimized.update(100) == False:
            break

        # Pause
        await asyncio.sleep(0)

    running = False

###########
# Network #
###########


def getUserId(pseudo):
    if pseudo is None:
        return None

    idsFound = [i for i, v in enumerate(state.userList)
                if v["pseudo"].lower() == pseudo.lower()]

    return idsFound[0] if len(idsFound) > 0 else None


def send(code, data):
    global msgLogin

    msg = {
        "code": code,
        "data": data
    }

    if code == MessageCode.LOGIN:
        msgLogin = msg
    else:
        if not netState.pseudoAccepted:
            msg["time"] = time.time()

        msgQueue.put_nowait(msg)


async def producer():
    global msgLogin

    while running:
        if not msgLogin is None:
            msg, msgLogin = msgLogin, None

            return msg
        elif not netState.pseudoAccepted or msgQueue.empty():
            await asyncio.sleep(0)
        else:
            return msgQueue.get_nowait()


async def producer_handler(ws):
    while running:
        message = await producer()
        if not message == None:
            print(f"[{timeToStr(time.time())}][NET SEND] {message}")
            try:
                await ws.send(json.dumps(message))
            except:
                # Reintroduce in msgQueue
                break


def on_login(data):
    global userList

    if isinstance(data, bool):
        if winNormal.isOpen() and data == False:
            if not promptPseudo.isOpen():
                promptPseudo.open("Study-withme: New pseudo", True)
        else:
            if not netState.renaming:
                netState.pseudoAccepted = data
            elif data == True:
                netState.renaming = False

            if data == True:
                state.pseudo = promptPseudo.pseudo

                promptPseudo.close()
                if not winNormal.isOpen():
                    winNormal.open()
                else:
                    winNormal.updatePseudo(state.pseudo)

    elif isinstance(data, str):
        state.userList.append({
            "pseudo": data,
            "state": UserState.REST
        })

        if not winNormal is None:
            winNormal.updateUserList()


def on_logout(data):
    id = getUserId(data)
    if not id == None:
        del state.userList[id]

    if not winNormal is None:
        winNormal.updateUserList()


def on_users(data):
    state.userList = data

    if not winNormal is None:
        winNormal.updateUserList()


def on_action(data):
    if "action" in data and "pseudo" in data:
        userState = UserState.WORK if data["action"] == ActionType.START else (
            UserState.BREAK if data["action"] == ActionType.BREAK else UserState.REST)

        id = getUserId(data["pseudo"])
        if not id is None:
            state.userList[id]["state"] = userState
            winNormal.updateUserState(data["pseudo"], userState)


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
    try:
        async for message in ws:
            await consumer(message)
    except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
        # print("Disconnection")
        pass


async def ping_handler(ws):
    while running:
        try:
            pong = await ws.ping()
            await asyncio.wait_for(pong, timeout=20)
            print("Ping --> Pong :)")

        except:
            print("Ping --> .... :(")

        finally:
            await asyncio.sleep(10)


async def handler(ws):
    consumer_task = asyncio.ensure_future(
        consumer_handler(ws))
    producer_task = asyncio.ensure_future(
        producer_handler(ws))
    # ping_task = asyncio.ensure_future(
    #     ping_handler(ws))

    done, pending = await asyncio.wait(
        [consumer_task, producer_task],
        # [consumer_task, producer_task, ping_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()


async def waitReconnection():
    if reconnectingAttempts == 1:
        waitSecs = 3
    elif reconnectingAttempts == 2:
        waitSecs = 10
    else:
        waitSecs = 30

    for i in range(waitSecs, 0, -1):
        if not running:
            break

        winNormal.updateStatus(f"Connection to the server lost. Reconnecting in {i}...")
        await asyncio.sleep(1)

    winNormal.updateStatus("Reconnecting...")


async def net():
    global connected, reconnectingAttempts

    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # print('running in a PyInstaller bundle')
        uri = "ws://study-withme.herokuapp.com"
    else:
        # print('running in a normal Python process')
        uri = "ws://localhost:31492"

    while running:
        try:
            async with websockets.connect(uri) as ws:
                if reconnectingAttempts > 0:
                    send(MessageCode.LOGIN, state.pseudo)

                connected = True
                reconnectingAttempts = 0

                winNormal.updateStatus("Connected")

                await handler(ws)

        except socket.gaierror:
            print("error socket")
            continue
        except ConnectionRefusedError:
            print("Refused connection")
            continue

        finally:
            if running:
                connected = False
                reconnectingAttempts += 1

                netState.pseudoAccepted = False

                winNormal.clearUserList()

                await waitReconnection()

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
