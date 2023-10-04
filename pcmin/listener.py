# Copyright (C) 2010-2015 Paul W. Frields and others.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
# Author: Paul W. Frields <stickster@gmail.com>

import dbus
import dbus.mainloop.glib
from enum import Enum


class CallState(Enum):
  UNKNOWN = 0
  DIALING = 1
  RINGING_OUT = 2
  RINGING_IN = 3
  ACTIVE = 4
  HELD = 5
  WAITING = 6
  TERMINATED = 7

class CallStateReason(Enum):
  UNKNOWN = 0
  OUTGOING_STARTED = 1
  INCOMING_NEW = 2
  ACCEPTED = 3
  TERMINATED = 4
  REFUSED_OR_BUSY = 5
  ERROR = 6
  AUDIO_SETUP_FAILED = 7
  TRANSFERRED = 8
  DEFLECTED = 9

CallDirection = Enum('CallDirection', {
  '📱?': 0,
  '📱⬅': 1,
  '📱➡': 2,
})


class PulseCasterListener:
    def __init__(self, ui):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()

        self.bus.add_signal_receiver(ui.callHandlerDEV,
                        bus_name='org.bluez',
                        interface_keyword='interface',
                        member_keyword='member',
                        path_keyword='path',
                        message_keyword='msg')


        self.bus.add_signal_receiver(ui.callHandler,
                                     dbus_interface='org.freedesktop.ModemManager1.Call',
                                     signal_name='StateChanged',
                                     sender_keyword='sender',
                                     path_keyword='path',
                                     interface_keyword='interface'
                                     )
