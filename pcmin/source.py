# Copyright (C) 2011-2019 Paul W. Frields and others.
# -*- coding: utf-8 -*-
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

import os, sys

try:
    from pcmin.config import *
except ModuleNotFoundError:
    sys.path.append(os.getcwd())
    sys.path.append(os.path.join(os.getcwd(), '..'))
    from pcmin.config import *

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, GObject, Gst
Gst.init(None)
import os

class PulseCasterSource:

    def __init__(self):
        self.liste = []
        debugPrint('out of __init__')
        
        
    def repopulate(self, pa, use_source=True, use_monitor=True):
        '''Repopulate the ComboBox for this object'''
        debugPrint('in repopulate')
        self.liste = []
        sources = pa.source_list()
        for source in sources:
            if source.monitor_of_sink_name == None:
                if use_source == True:
                    self.liste.append(source.name)
       
            else:
                if use_monitor == True:
                    self.liste.append(source.name)
                 
        self.pulsesrc = self.liste[0]
        debugPrint('out of repopulate')

  
 