import sys
import os
import dbus
import tempfile
from pulsectl import Pulse
from datetime import datetime

try:
    from pcmin.config import *
    from pcmin.listener import *
    from pcmin.source import *
except ModuleNotFoundError:
    sys.path.append(os.getcwd())
    sys.path.append(os.path.join(os.getcwd(), '..'))
    from pcmin.config import *
    from pcmin.listener import *
    from pcmin.source import *


import gi
from gi.repository import Gtk, Gst, GObject, Gio
gi.require_version("Gtk", "3.0")
gi.require_version("Gst", "1.0")

Gst.init(None)


class PulseCasterUI(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(
            self,
            application_id="apps.org.pulsecaster.PulseCaster",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self.connect("activate", self.on_activate)

    def on_activate(self, app):

        self.createRecordingsFolder()
        self.pa = Pulse(client_name=NAME)

        self.user_vox = PulseCasterSource()
        self.subject_vox = PulseCasterSource()

        self.repop_sources()

        self.listener = PulseCasterListener(self)
        self.file_prefix = 'deneme2'

        self.bus = dbus.SystemBus()

    def callHandler(self, old_state, new_state, reason, sender, path, interface):

        debugPrint(
            f'{CallState(old_state)} -> {CallState(new_state)}, reason: {CallStateReason(reason)}')

        if CallState(new_state) == CallState.ACTIVE:
            details = self.bus.get_object(sender, path).GetAll(
                interface, dbus_interface='org.freedesktop.DBus.Properties')
            d = datetime.now().strftime('%Y-%m-%d_%H.%M.%S')
            self.file_prefix = f"{d}_{(CallDirection(details['Direction']).name)}_{(details['Number'])}"
            self.startRecording()

        elif CallState(new_state) == CallState.TERMINATED:
            self.endRecording()

    def callHandlerDEV(self, *args, **kwargs):
        try:
            powered = bool(dict(args[1])[dbus.String('Powered')])
        except KeyError:
            return

        if powered:
            self.startRecording()
        else:
            self.stopRecording()

    def repop_sources(self, *args):
        self.user_vox.repopulate(self.pa, use_source=True, use_monitor=False)
        self.subject_vox.repopulate(
            self.pa, use_source=False, use_monitor=True)

    def startRecording(self, *args):

        self.combiner = Gst.Pipeline()
        self.lsource = Gst.ElementFactory.make("pulsesrc", "lsrc")
        self.lsource.set_property("device", self.user_vox.pulsesrc)
        self.rsource = Gst.ElementFactory.make("pulsesrc", "rsrc")
        self.rsource.set_property("device", self.subject_vox.pulsesrc)

        self._default_caps = Gst.Caps.from_string(
            "audio/x-raw, " "rate=(int)%d" % (AUDIORATE)
        )
        self.adder = Gst.ElementFactory.make("adder", "mix")
        self.lfilter = Gst.ElementFactory.make("capsfilter", "lfilter")
        self.rfilter = Gst.ElementFactory.make("capsfilter", "rfilter")
        debugPrint("audiorate: %d" % AUDIORATE)

        # Create temporary file
        (self.tempfd1, self.temppath1) = tempfile.mkstemp(
            prefix="%s-1-tmp." % (NAME)
        )
        (self.tempfd2, self.temppath2) = tempfile.mkstemp(
            prefix="%s-2-tmp." % (NAME)
        )
        self.tempfile1 = os.fdopen(self.tempfd1)
        self.tempfile2 = os.fdopen(self.tempfd2)
        debugPrint(
            "tempfiles: %s (fd %s), %s (fd %s)"
            % (self.temppath1, self.tempfd1, self.temppath2, self.temppath2)
        )
        # We're in expert mode
        # Disregard vorbis, use WAV
        self.encoder1 = Gst.ElementFactory.make("wavenc", "enc1")
        self.encoder2 = Gst.ElementFactory.make("wavenc", "enc2")
        self.filesink1 = Gst.ElementFactory.make("filesink", "fsink1")
        self.filesink1.set_property("location", self.temppath1)
        self.filesink2 = Gst.ElementFactory.make("filesink", "fsink2")
        self.filesink2.set_property("location", self.temppath2)
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

    def stopRecording(self):
        self.combiner.set_state(Gst.State.NULL)
        self.saveRecordings()
        self.file_prefix = ''

    def on_close(self, *args):
        try:
            self.pa.disconnect()
        except:
            pass
        self.quit()

    def saveRecordings(self):
        self._copy_temp_to_perm(self.file_prefix)

        expert_message = "WAV files are written here:"
        expert_message += "\n%s\n%s" % (
            RECORDINGS_DIR + self.file_prefix + "-1.wav",
            RECORDINGS_DIR + self.file_prefix + "-2.wav",
        )
        debugPrint(expert_message)

        self._remove_tempfile(self.tempfile1, self.temppath1)
        self._remove_tempfile(self.tempfile2, self.temppath2)

    def createRecordingsFolder(self):
        if not os.path.isdir(RECORDINGS_DIR):
            print(f"Creating {RECORDINGS_DIR}")
            os.mkdir(RECORDINGS_DIR)

    def _copy_temp_to_perm(self, file_prefix):
        for i in (1, 2):
            permfile = open(RECORDINGS_DIR + file_prefix +
                            "-" + str(i) + ".wav", "wb")
            tf = eval("self.tempfile" + str(i))
            tf.close()
            tempfile = open(eval("self.temppath" + str(i)), "rb")
            permfile.write(tempfile.read())
            permfile.close()

    def _remove_tempfile(self, tempfile, temppath):
        tempfile.close()
        os.remove(temppath)


if __name__ == "__main__":
    pulseCaster = PulseCasterUI()
    pulseCaster.run(sys.argv)
