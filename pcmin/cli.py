import os
import dbus
import tempfile
from pulsectl import Pulse
from logger import logger
from dbus.mainloop.glib import DBusGMainLoop

from config import *
from enums import *
from utils import *

import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib
Gst.init(None)


class PCMin():
    def __init__(self):
        self.name_devices = ['', '']
        self.temp_filenames = ['', '']
        self.file_prefix_rec = ''

        self.loop_glib = GLib.MainLoop()
        self.loop_dbus = DBusGMainLoop()
        self.bus = dbus.SystemBus(mainloop=self.loop_dbus)
        self.pa = Pulse(client_name=NAME)

        self._repopulate_sources()
        self._add_call_signal_reciever()
        self._create_recordings_folder()

    def run(self):
        self.loop_glib.run()

    def _call_handler(self, state_new, state_old, reason, sender, path, interface):

        logger.debug(
            f"CallState: {CallState(state_new)} -> {CallState(state_old)}, Reason: {CallStateReason(reason)}")

        if CallState(state_old) == CallState.ACTIVE:
            self._repopulate_sources()

            call_details = dbus_get_properties(
                self.bus, sender, path, interface)
            prefix_date = create_date()
            call_direction = CallDirection(call_details['Direction']).name
            call_number = call_details['Number']
            logger.debug(
                f"Call Direction: {call_direction}, Number: {call_number}")

            self.file_prefix_rec = f"{prefix_date}_{call_direction}_{call_number}"
            self._start_recording()

        elif CallState(state_old) == CallState.TERMINATED:
            self._stop_recording()

    def _call_handler_DEV(self, *args, **kwargs):
        self.file_prefix_rec = create_date()

        try:
            powered = bool(dict(args[1])[dbus.String("Powered")])
        except KeyError:
            return

        if powered:
            self._start_recording()
        else:
            self._stop_recording()

    def _add_call_signal_reciever(self):
        self.bus.add_signal_receiver(self._call_handler,
                                     dbus_interface='org.freedesktop.ModemManager1.Call',
                                     signal_name='StateChanged',
                                     sender_keyword='sender',
                                     path_keyword='path',
                                     interface_keyword='interface'
                                     )

        self.bus.add_signal_receiver(self._call_handler_DEV,
                                     bus_name='org.bluez',
                                     interface_keyword='interface',
                                     member_keyword='member',
                                     path_keyword='path',
                                     message_keyword='msg')

    def _get_default_source_name(self, use_monitor):
        source_name = ''
        sources = self.pa.source_list()
        for source in sources:
            if source.monitor_of_sink_name == None:
                if not use_monitor:
                    source_name = source.name
            else:
                if use_monitor:
                    source_name = source.name

        return source_name

    def _repopulate_sources(self):
        for vox_id in (0, 1):
            self.name_devices[vox_id] = self._get_default_source_name(
                use_monitor=bool(vox_id))
            logger.debug(f'Rec Device {vox_id}: {self.name_devices[vox_id]}')

    def _start_recording(self):
        # Create temporary file
        for vox_id in (0, 1):
            self._create_tempfile(vox_id)

        # Create pipeline and configure
        self.combiner = Gst.Pipeline()
        self.lsource = Gst.ElementFactory.make("pulsesrc", "lsrc")
        self.lsource.set_property("device", self.name_devices[0])
        self.rsource = Gst.ElementFactory.make("pulsesrc", "rsrc")
        self.rsource.set_property("device", self.name_devices[1])

        self._default_caps = Gst.Caps.from_string(
            "audio/x-raw, " "rate=(int)%d" % (AUDIORATE)
        )
        self.adder = Gst.ElementFactory.make("adder", "mix")
        self.lfilter = Gst.ElementFactory.make("capsfilter", "lfilter")
        self.rfilter = Gst.ElementFactory.make("capsfilter", "rfilter")

        self.encoder1 = Gst.ElementFactory.make("wavenc", "enc1")
        self.encoder2 = Gst.ElementFactory.make("wavenc", "enc2")
        self.filesink1 = Gst.ElementFactory.make("filesink", "fsink1")
        self.filesink1.set_property(
            "location", self.temp_filenames[0])
        self.filesink2 = Gst.ElementFactory.make("filesink", "fsink2")
        self.filesink2.set_property(
            "location", self.temp_filenames[1])
        for e in (
            self.lsource,
            self.lfilter,
            self.rsource,
            self.rfilter,
            self.encoder1,
            self.encoder2,
            self.filesink1,
            self.filesink2,
        ):
            self.combiner.add(e)
        self.lsource.link(self.lfilter)
        self.lfilter.link(self.encoder1)
        self.encoder1.link(self.filesink1)
        self.rsource.link(self.rfilter)
        self.rfilter.link(self.encoder2)
        self.encoder2.link(self.filesink2)

        self.combiner.set_state(Gst.State.PLAYING)
        logger.debug('Recording started.')

    def _stop_recording(self):
        logger.debug('Recording ended.')
        self.combiner.set_state(Gst.State.NULL)

        for vox_id in (0, 1):
            self._save_recording(vox_id)

        self.file_prefix_rec = ""

    def _on_close(self):
        try:
            self.pa.disconnect()
        except:
            pass
        self.loop_glib.quit()

    def _save_recording(self, vox_id):
        self._relocate_recording(vox_id)
        self._delete_tempfile(vox_id)

    def _create_recordings_folder(self):
        if not os.path.isdir(RECORDINGS_DIR):
            logger.debug(f"Creating {RECORDINGS_DIR}")
            os.mkdir(RECORDINGS_DIR)
            logger.debug(f'Recordings folder created ({RECORDINGS_DIR})')
            return

        logger.debug(f'Recordings folder already exists ({RECORDINGS_DIR})')

    def _relocate_recording(self, vox_id):

        temp_path = self.temp_filenames[vox_id]
        file_recording = open(temp_path, 'rb')
        data_recording = file_recording.read()

        permanent_filename = f'{RECORDINGS_DIR}{self.file_prefix_rec}-{vox_id}.wav'
        permanent_file = open(permanent_filename, "wb")
        permanent_file.write(data_recording)
        permanent_file.close()
        logger.debug(f'Rec {vox_id} relocated to "{permanent_filename}"')

    def _delete_tempfile(self, vox_id):
        temp_path = self.temp_filenames[vox_id]
        os.remove(temp_path)
        logger.debug(f'Tempfile deleted. ({temp_path})')
        self.temp_filenames[vox_id] = ''

    def _create_tempfile(self, vox_id):
        _, temp_path = tempfile.mkstemp(prefix=f"{NAME}-{vox_id}-tmp.")
        self.temp_filenames[vox_id] = temp_path
        logger.debug(f"Rec ID: {vox_id}, Tempfile: {temp_path}")
