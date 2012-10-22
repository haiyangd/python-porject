#!/usr/bin/python
#
# tui.py - Copyright (C) 2012 Red Hat, Inc.
# Written by Fabian Deutsch <fabiand@redhat.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.  A copy of the GNU General Public License is
# also available at http://www.gnu.org/copyleft/gpl.html.

"""
The urwid TUI base library
"""

import urwid

import logging
import timeit

import ovirt.node
import ovirt.node.plugins
import ovirt.node.ui
import ovirt.node.ui.widgets
import ovirt.node.ui.builder
import ovirt.node.exceptions
import ovirt.node.utils

LOGGER = logging.getLogger(__name__)


class UrwidTUI(object):
    app = None

    __pages = {}
    __hotkeys = {}

    __loop = None
    __main_frame = None
    __menu = None
    __page_frame = None

    __widget_stack = []

    header = u"\n Configuration TUI\n"
    footer = u"Press ctrl+c to exit"

    palette = [('header', 'white', 'dark blue'),
               ('table', 'dark gray', ''),
               ('table.header', 'dark gray, bold', ''),
               ('table.entry', 'dark gray', ''),
               ('table.entry:focus', 'white', 'light blue', 'standout'),
               ('main.menu', 'black', ''),
               ('main.menu.frame', 'light gray', ''),
               ('notice', 'light red', ''),
               ('plugin.widget.entry', 'dark gray', ''),
               ('plugin.widget.entry.disabled', 'dark gray', 'light gray'),
               ('plugin.widget.entry.label', 'dark gray, bold', ''),
               ('plugin.widget.entry.frame', 'light gray', ''),
               ('plugin.widget.entry.frame.invalid', 'dark red', ''),
               ('plugin.widget.notice', 'light red', ''),
               ('plugin.widget.header', 'black, bold', ''),
               ('plugin.widget.divider', 'dark gray', ''),
               ('plugin.widget.button', 'dark blue', ''),
               ('plugin.widget.button.disabled', 'light gray', ''),
               ('plugin.widget.label', 'dark gray', ''),
               ('plugin.widget.label.keyword', 'dark gray, bold', ''),
               ('plugin.widget.progressbar.box', 'light gray', ''),
               ('plugin.widget.progressbar.uncomplete', '', ''),
               ('plugin.widget.progressbar.complete', '', 'light gray'),
               ('plugin.widget.options.label', 'dark gray, bold', ''),
               ]

    def __init__(self, app):
        LOGGER.info("Creating urwid tui for '%s'" % app)
        self.app = app

    def __build_menu(self):
        self.__menu = ovirt.node.ui.widgets.PluginMenu(self.__pages)

        def menu_item_changed(plugin):
            self.display_plugin(plugin)
        urwid.connect_signal(self.__menu, 'changed', menu_item_changed)

    def __create_screen(self):
        self.__build_menu()
        self.__page_frame = urwid.Frame(urwid.Filler(urwid.Text("")))
        self.__menu.set_focus(0)

        self.__notice = urwid.Text("Note: ")
        self.__notice_filler = urwid.Filler(self.__notice)
        self.__notice_attrmap = urwid.AttrMap(self.__notice_filler, "notice")

        menu_frame_columns = urwid.Columns([("weight", 0.5, self.__menu),
                              self.__page_frame], 4)

        body = urwid.Pile([("fixed", 3, self.__notice_attrmap),
                           menu_frame_columns
                        ])

        header = urwid.Text(self.header, wrap='clip')
        header = urwid.AttrMap(header, 'header')
        footer = urwid.Text(self.footer, wrap='clip')
        return urwid.Frame(body, header, footer)

    def display_plugin(self, plugin):
        timer = timeit.Timer()
        page = ovirt.node.ui.builder.page_from_plugin(self, plugin)
        self.display_page(page)
        LOGGER.debug("Build and displayed page in %ss" % timer.timeit())

    def display_page(self, page):
        # FIXME why is this fixed?
        filler = urwid.Filler(page, ("fixed top", 1), height=30)
#        filler = urwid.Filler(page)
        self.__page_frame.body = filler

    def display_dialog(self, body, title):
        LOGGER.debug("Displaying dialog: %s / %s" % (body, title))
        filler = urwid.Filler(body, ("fixed top", 1), height=20)
        dialog = ovirt.node.ui.widgets.ModalDialog(title, filler, "esc",
                                                   self.__loop.widget)
        urwid.connect_signal(dialog, "close", lambda: self.close_dialog(dialog))
        self.__loop.widget = dialog
        self.__widget_stack.append(dialog)
        return dialog

    def close_dialog(self, dialog):
        # FIXME stack to allow more than one dialog
        if type(self.__loop.widget) is ovirt.node.ui.widgets.ModalDialog:
            if dialog == self.__widget_stack[-1]:
                self.__widget_stack.pop()
                if len(self.__widget_stack) > 0:
                    self.__loop.widget = self.__widget_stack[:-1]
                else:
                    self.__loop.widget = self.__main_frame
            LOGGER.debug("Dialog closed")

    def popup(self, title, msg, buttons=None):
        LOGGER.debug("Launching popup")
        body = urwid.Filler(urwid.Text(msg))
        self.display_dialog(body)

    def __filter_hotkeys(self, keys, raw):
        key = str(keys)

        if type(self.__loop.widget) is ovirt.node.ui.widgets.ModalDialog:
            LOGGER.debug("Modal dialog escape: %s" % key)
            if self.__loop.widget.escape_key in keys:
                self.close_dialog(self.__widget_stack[-1])
                return

        if key in self.__hotkeys.keys():
            LOGGER.debug("Running hotkeys: %s" % key)
            self.__hotkeys[key]()

        LOGGER.debug("Keypress: %s" % key)

        return keys

    def __register_default_hotkeys(self):
        self.register_hotkey(["esc"], self.quit)
        self.register_hotkey(["q"], self.quit)

    def draw_screen(self):
        self.__loop.draw_screen()

    def watch_pipe(self, cb):
        """Return a fd to be used as stdout, cb called for each line
        """
        return self.__loop.watch_pipe(cb)

    def notify(self, category, msg):
        LOGGER.info("UI notification (%s): %s" % (category, msg))
        # FIXME do notification

    def suspended(self):
        """Supspends the screen to do something in the foreground
        """
        class SuspendedScreen(object):
            def __init__(self, loop):
                self.__loop = loop

            def __enter__(self):
                self.__loop.screen.stop()

            def __exit__(self, a, b, c):
                self.__loop.screen.start()
        return SuspendedScreen(self.__loop)

    def register_plugin(self, title, plugin):
        """Register a plugin to be shown in the UI
        """
        self.__pages[title] = plugin

    def register_hotkey(self, hotkey, cb):
        """Register a hotkey
        """
        if type(hotkey) is str:
            hotkey = [hotkey]
        LOGGER.debug("Registering hotkey '%s': %s" % (hotkey, cb))
        self.__hotkeys[str(hotkey)] = cb

    def quit(self):
        """Quit the UI
        """
        LOGGER.info("Quitting, exitting mainloop")
        raise urwid.ExitMainLoop()

    def run(self):
        """Run the UI
        """
        self.__main_frame = self.__create_screen()
        self.__register_default_hotkeys()

        self.__loop = urwid.MainLoop(self.__main_frame,
                              self.palette,
                              input_filter=self.__filter_hotkeys)
        self.__loop.run()