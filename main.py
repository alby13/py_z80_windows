#-----------------------------------------------------------------------------
"""
PyZ80: Z80 platform Emulator
"""
#-----------------------------------------------------------------------------

import sys
import logging
import conio
import cli
import util
import jace
import tec1

#-----------------------------------------------------------------------------

_version_str = 'PyZ80: Python Z80 Platform Emulator 0.11 Windows'

#-----------------------------------------------------------------------------

class application:

    def __init__(self):
        self.menu_targets = (
            ('jace', 'Jupiter Ace', util.cr, self.target_jace, None),
            ('tec1', 'Talking Electronics TEC-1', util.cr, self.target_tec1, None),
        )
        self.menu_root = (
            ('exit', 'exit the application', util.cr, self.exit, None),
            ('help', 'display general help', util.cr, self.general_help, None),
            ('target', 'select a target', None, None, self.menu_targets),
            ('version', 'display version information', util.cr, self.version, None),
        )

        # create the cli
        self.io = conio.console()
        self.cli = cli.cli(self)
        self.main_menu()

    def cleanup(self):
        """application cleanup prior to exit"""
        self.io.close()

    def main_menu(self):
        self.cli.set_root(self.menu_root)
        self.cli.set_prompt('\npyz80> ')

    def put(self, data):
        """console ouput for leaf functions"""
        print(data, end='')  # Use print() instead of self.io.put()
        sys.stdout.flush()  # Ensure output is immediately displayed

    def run(self):
        self.cli.run()

    def exit(self, app, args):
        app.cli.exit()

    def version(self, app, args):
        """display a version string"""
        app.put('\n\n%s\n' % _version_str)

    def target_jace(self, app, args):
        app.put('\n\nemulating "Jupiter ACE"\n')
        self.current_target = jace.jace(app) # Store the target instance
        app.cli.set_prompt('\njace> ')
        #jace.jace(app)

    def target_tec1(self, app, args):
        app.put('\n\nemulating "Talking Electronics TEC 1"\n')
        #self.current_target = tec1.tec1(app) # Store the target instance
        #app.cli.set_prompt('\ntec1> ')
        #tec1.tec1(app)

    def general_help(self, app, args):
        app.cli.func_help(util.general)

#-----------------------------------------------------------------------------

def main():
    app = application()
    app.put('\n%s\n' % _version_str)
    try:
        app.run()
    except KeyboardInterrupt:
        print("Z80 Emulation stopped by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        app.cleanup()

#-----------------------------------------------------------------------------

if __name__ == '__main__':
    logging.getLogger('').addHandler(logging.StreamHandler())
    main()

#-----------------------------------------------------------------------------
