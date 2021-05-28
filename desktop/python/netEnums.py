from enum import IntEnum

class NetError(IntEnum):
    CONNECTION_REFUSED = 0
    SOCKET_ERROR = 1

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
