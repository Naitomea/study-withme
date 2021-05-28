# TimeUtils
import math
import time


def timeToStr(time, hour=True):
    h = math.floor(time % 86400 / 3600)
    if hour:
        m = math.floor(time % 3600 / 60)
    else:
        m = math.floor(time / 60)
    s = math.floor(time % 60)

    if h < 10:
        h = "0" + str(h)
    if m < 10:
        m = "0" + str(m)
    if s < 10:
        s = "0" + str(s)

    if hour:
        return f"{h}:{m}:{s}"
    else:
        return f"{m}:{s}"


def getSyncTime(ctime=None):
    syncTime = 4200 - (time.time() if ctime is None else ctime) % 4200
    if syncTime > 600:
        return syncTime - 600, False
    else:
        return 600 - syncTime, True
