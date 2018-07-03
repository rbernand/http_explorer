class ScreenData:
    def __init__(self, lstscr, ddlscr):
        self._height = 0
        self._width = 0
        self._cursor = 0
        self._page = 0
        self._lstscr = lstscr
        self._ddlscr = ddlscr
        self._filter = ''

    def refresh(self):
        self._height, self._width = self._lstscr.getmaxyx()

    @property
    def filter(self):
        return self._filter

    @filter.setter
    def filter(self, value):
        self._filter = value

    @property
    def lstscr(self):
        return self._lstscr

    @property
    def ddlscr(self):
        return self._ddlscr

    @property
    def h(self):
        return self._height

    @property
    def w(self):
        return self._width

    @property
    def cursor(self):
        return self._cursor

    @cursor.setter
    def cursor(self, value: int):
        self._cursor = max(0, min(value, self._height - 1))

    @property
    def page(self):
        return self._page

    @page.setter
    def page(self, value: int):
        self._page = max(0, min(value, self._height - 1))
