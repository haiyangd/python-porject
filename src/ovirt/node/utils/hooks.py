#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# hooks.py - Copyright (C) 2014 Red Hat, Inc.
# Written by Ryan Barry <rbarry@redhat.com>
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
Manage running installer hooks
"""

from ovirt.node import base, log
from ovirt.node.utils import process
import os

LOGGER = log.getLogger(__name__)


class Hooks(base.Base):
    """A utility class which executes files for additional configuration
    beyond the normal install
    """

    @staticmethod
    def post_auto_install():
        hooks_directory = "/etc/ovirt-config-boot.d/"
        Hooks.__run(hooks_directory)

    @staticmethod
    def __run(hooks_directory):
        for hook in os.listdir(hooks_directory):
            script = os.path.join(hooks_directory, hook)
            if script.endswith(".py"):
                LOGGER.debug("Running hook %s" % script)
                output = process.check_output(["python", script])
                [LOGGER.debug("%s: %s" % (script, line)) for line in
                    output]
            else:
                LOGGER.debug("Running hook %s" % script)
                output = process.check_output("%s &> /dev/null" % script,
                                              shell=True)
                [LOGGER.debug("%s: %s" % (script, line)) for line in
                    output]
