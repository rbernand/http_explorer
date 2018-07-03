import sys
import curses
import argparse
import threading
import urllib.parse
from functools import partial
from datetime import datetime, timedelta
from collections import namedtuple
from contextlib import contextmanager

import requests
from lxml import html
from requests.auth import HTTPBasicAuth

from .screendata import ScreenData
from .element import HTTPElement


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("-p", '--password', default=None)
    parser.add_argument("-u", '--user', default=None)
    args = parser.parse_args(sys.argv[1:])
    return args


def get_elements_list(site):
    ret = requests.get(site.url, auth=site.auth)
    print(ret)
    tree = html.fromstring(ret.text)
    return [HTTPElement(x) for x in tree.xpath("/html/body/table/tr")[2:-1]]


@contextmanager
def setup_ncurses():
    try:
        curses.noecho()
        curses.cbreak()
        # Invisible cursor
        curses.curs_set(False)

        # Color initialisation
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)

        # create windows
        c = curses.COLS
        l = curses.LINES
        lstscr = curses.newwin(l - 1, c, 0, 0)
        ddlscr = curses.newwin(1, c, l - 1, 0)

        lstscr.keypad(1)
        yield lstscr, ddlscr
    finally:
        curses.echo()
        curses.nocbreak()
        curses.endwin()
        curses.curs_set(True)


def get_elements(url):
    elements = get_elements_list(url)
    return elements, len(elements)


def print_elements(elements, screendata, stdscr):
    stdscr.attron(curses.color_pair(1))
    s = slice(
        (screendata.h - 1) * screendata.page, (screendata.h - 1) * (screendata.page + 1)
    )
    for pos, elem in zip(range(screendata.h - 1), elements[s]):
        with highlight_current_line(1, 2, pos == screendata.cursor, stdscr):
            stdscr.addstr(
                pos,
                0,
                "{elem.type} {elem.name:.{x}s}".format(elem=elem, x=screendata.w - 6),
            )


@contextmanager
def highlight_current_line(normal_color, highlight_color, condition, stdscr):
    if condition:
        stdscr.attron(curses.color_pair(highlight_color))
    yield
    if condition:
        stdscr.attron(curses.color_pair(normal_color))


def print_progress(name, value, ddlscr):
    ddlscr.clear()
    _, x = ddlscr.getmaxyx()
    message = f"Downloading: {name:s}{value:{x - 2 - 13 - len(name)}.2f}%"
    pos = int(value * x / 100)
    ddlscr.addstr(0, 0, message[:pos], curses.A_REVERSE)
    ddlscr.addstr(0, pos, message[pos:])
    ddlscr.refresh()


def download_file(site, elem, ddlscr):
    ret = requests.get(
        urllib.parse.urljoin(site.url, elem.url),
        auth=site.auth,
        stream=True,
    )
    print_progress(elem.name, 0, ddlscr)
    with open(elem.name, "wb+") as output:
        try:
            total_length = int(ret.headers["Content-Length"])
            timestamp = datetime.now()
            csize = 0
            for chunk in ret.iter_content(4096):
                output.write(chunk)
                csize += 4096
                if datetime.now() >= timestamp + timedelta(0, 1):
                    ddlscr.refresh()
                    print_progress(
                        elem.name, csize * 100 / total_length, ddlscr
                    )
                    timestamp = datetime.now()
        except KeyError:
            ddlscr.addstr(0, 0, "No progress available")
            ddlscr.refresh()
            output.write(ret.content)
        finally:
            ret.close()
    ddlscr.clear()
    ddlscr.addstr(0, 0, "Download complete.")
    ddlscr.refresh()
    return


def exec_key(key, elem, site, screendata):
    if key in (curses.KEY_DOWN, ord("j")):
        screendata.cursor = screendata.cursor + 1
    elif key in (curses.KEY_UP, ord("k")):
        screendata.cursor = screendata.cursor - 1
    elif key in (curses.KEY_LEFT, ord("h")):
        screendata.page = screendata.page - 1
    elif key in (curses.KEY_RIGHT, ord("l")):
        screendata.page = screendata.page + 1
    elif key in (curses.KEY_ENTER, ord("d")):
        if elem.isdir():
            return True
        else:
            t = threading.Thread(
                target=download_file, args=(site, elem, screendata.ddlscr), daemon=True
            )
            t.start()
    elif key in (ord("/"),):
        filt = ''
        key = 0
        while key != ord('\n'):
            msg = f"/{filt:<{screendata.w - 2}s}"
            screendata.lstscr.addstr(screendata.h - 1, 0, msg, curses.color_pair(3))
            key = screendata.lstscr.getch()
            filt += chr(key)
        screendata.filter = filt
    return False


def main_loop(args, stdscr, ddlscr):
    site = namedtuple('Site', ['url', 'auth'])(args.url, HTTPBasicAuth(args.user, args.password))
    sdata = ScreenData(stdscr, ddlscr)
    key = 0
    elements, nb_elements = get_elements(site)
    url = args.url
    while key != ord("q"):
        sdata.refresh()
        stdscr.clear()
        cursor = (sdata.h - 1) * sdata.page + sdata.cursor + 1
        menu_info = f"Scanning: {url:<{sdata.w - 10 - len(str(cursor)) - 3 - len(str(nb_elements))}s} {cursor:}/{nb_elements}"
        stdscr.addstr(sdata.h - 1, 0, menu_info, curses.color_pair(3))
        print_elements(elements, sdata, stdscr)
        stdscr.refresh()
        key = stdscr.getch()
        if exec_key(key, elements[cursor - 1], site, sdata):
            url = urllib.parse.urljoin(url, elements[cursor - 1].url)
            elements, nb_elements = get_elements(site)
            sdata = ScreenData(stdscr, ddlscr)


def main():
    args = parse_args(sys.argv)
    stdscr = curses.initscr()
    with setup_ncurses() as (lstscr, ddlscr):
        main_loop(args, lstscr, ddlscr)


if __name__ == "__main__":
    main()
