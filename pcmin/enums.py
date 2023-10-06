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

