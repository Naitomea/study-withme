from abc import abstractmethod
import PySimpleGUI as sg


class Window:
    def __init__(self, layout, title="", show=False):
        self._win = None
        self._layout = layout
        self._title = title

        if show:
            self.show()

    def _initLayout(self):
        self._layout = list(self._layout)

    def open(self, title=None, modal=False):
        if not title == None:
            self._title = title

        self._initLayout()
        self._win = sg.Window(self._title, self._layout, modal=modal)

    def close(self):
        if self._win is None:
            return

        self._win.close()
        self._win = None

    def update(self, waitTime=None):
        if self._win is None or self._win.was_closed():
            return None, None
        return self._win.read(waitTime)

    def isOpen(self):
        return not self._win == None and not self._win.was_closed()

    # Events
    def _call_event(self, event, values=None):
        if callable(event):
            if values is None:
                event()
            else:
                event(values)

    # Built-in Operators
    def __getitem__(self, name):
        return self._win[name] if self.isOpen() else None
