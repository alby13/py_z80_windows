#-----------------------------------------------------------------------------
"""
Console IO

Provides non-blocking, non-echoing access to the console interface.
"""
#-----------------------------------------------------------------------------

import os
import msvcrt
import sys
import ctypes
from ctypes import wintypes

#termiWin = ctypes.CDLL('C:/tmp/pyz80/termiWin.dll')

#-----------------------------------------------------------------------------
# when otherwise idle, allow other things to run

_poll_timeout = 0.1 # secs

#-----------------------------------------------------------------------------

CHAR_NULL  = 0x00
CHAR_BELL  = 0x07
CHAR_TAB   = 0x09
CHAR_CR    = 0x0a
CHAR_DOWN  = 0x10
CHAR_UP    = 0x11
CHAR_LEFT  = 0x12
CHAR_RIGHT = 0x13
CHAR_END   = 0x14
CHAR_HOME  = 0x15
CHAR_ESC   = 0x1b
CHAR_SPACE = 0x20
CHAR_QM    = 0x3f
CHAR_BS    = 0x7f
CHAR_DEL   = 0x7e

#-----------------------------------------------------------------------------
#
# Modification Notes (July 30, 2024):
# We create a custom way to manage the console mode on Windows. 
# Since msvcrt doesn’t provide a direct method to save and restore the console mode, 
# we can implement a workaround by using the Windows API to get and set console modes.
#
#-----------------------------------------------------------------------------

# Windows API constants
ENABLE_ECHO_INPUT = 0x0004
ENABLE_LINE_INPUT = 0x0002
ENABLE_PROCESSED_INPUT = 0x0001

# Windows API functions
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

def get_console_mode(handle):
    mode = wintypes.DWORD()
    if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        raise ctypes.WinError(ctypes.get_last_error())
    return mode.value

def set_console_mode(handle, mode):
    if not kernel32.SetConsoleMode(handle, mode):
        raise ctypes.WinError(ctypes.get_last_error())

class console:
    def __init__(self):
        """set the console to non-blocking, non-echoing"""
        self.handle = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
        self.saved_mode = get_console_mode(self.handle)
        new_mode = self.saved_mode & ~(ENABLE_ECHO_INPUT | ENABLE_LINE_INPUT)
        set_console_mode(self.handle, new_mode)

    def close(self):
        """restore original console settings"""
        set_console_mode(self.handle, self.saved_mode)

    def anykey(self):
        """poll for any key - return True when pressed"""
        return msvcrt.kbhit()

    def get(self):
        """get console input - return ascii code or None if no input"""
        if msvcrt.kbhit():
            ch = msvcrt.getch()
            if ch == b'\xe0': # Handle arrow keys
                ch = msvcrt.getch()
                if ch == b'H':
                    return CHAR_UP
                elif ch == b'P':
                    return CHAR_DOWN
                elif ch == b'K':
                    return CHAR_LEFT
                elif ch == b'M':
                    return CHAR_RIGHT
            elif ch == b'\r':  # Enter key
                return CHAR_CR
            elif ch == b'\x08': # Backspace key
                return CHAR_BS # Return a specific code for backspace
            else:
                return ord(ch)
        return None # Return None when no input

    def put(self, data):
        """output a string to console"""
        sys.stdout.write(data)
        sys.stdout.flush()

#-----------------------------------------------------------------------------
