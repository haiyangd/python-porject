#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# ovirt-config-installer.py - Copyright (C) 2012 Red Hat, Inc.
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
Create an setup application instance an start it.
"""

from ovirt.node import app, installer, plugins


if __name__ == '__main__':
    app = app.Application(installer)
    app.run()


class Plugin(plugins.NodePlugin):
    transactions = None

    def __init__(self, application):
        super(Plugin, self).__init__(application)
        application.ui.with_menu = False

    def name(self):
        return "installer"

    def has_ui(self):
        return False