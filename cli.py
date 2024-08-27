#-----------------------------------------------------------------------------
"""
Command Line Interface

Implements a CLI with:

* hierarchical menus
* command completion
* command history
* context sensitive help
* command editing

Notes:

Menu Format: (name, descr, help, leaf, submenu)
Function Help Format: (parm, descr)

"""
#-----------------------------------------------------------------------------

import sys
import conio
import time

#-----------------------------------------------------------------------------

class command:

    def __init__(self, app):
        """initialise to an empty command string"""
        self.app = app
        self.clear()

    def clear(self):
        """clear the command string"""
        self.cmd = []
        self.cursor = 0

    def set(self, cmd):
        """set the command string to a new value"""
        self.cmd = list(cmd)
        self.cursor = len(cmd)

    def get(self):
        """return the current command string"""
        return ''.join(self.cmd)

    def backspace(self):
        """erase the character to the left of the cursor position"""
        if self.cursor > 0:
            del self.cmd[self.cursor - 1]
            self.cursor -= 1
            self.app.io.put('\b \b')  # Send backspace, space, backspace 
            sys.stdout.flush()        # Flush output to update the console immediately

    def delete(self):
        """erase the character at the cursor position"""
        if self.cursor < len(self.cmd):
            del self.cmd[self.cursor]

    def add(self, x):
        """add character(s) to the command string"""
        for c in x:
            self.cmd.insert(self.cursor, c)
            self.cursor += 1

    def left(self):
        """move the cursor left"""
        if self.cursor > 0:
            self.cursor -= 1

    def right(self):
        """move the cursor right"""
        if self.cursor < len(self.cmd):
            self.cursor += 1

    def home(self):
        """move the cursor to the home"""
        self.cursor = 0

    def end(self):
        """move the cursor to the end"""
        self.cursor = len(self.cmd)

    def erase(self):
        """erase a character from the tail of the command string"""
        del self.cmd[-1:]
        # ensure the cursor is valid
        self.end()

    def render(self):
        # Move to the beginning of the line and clear it
        self.app.io.put('\r\x1b[K')

        # Write the prompt and command
        full_line = self.app.cli.prompt + self.get()
        sys.stdout.write(full_line)   

        # Move cursor to correct position
        cursor_position = len(self.app.cli.prompt) + self.cursor
        sys.stdout.write(f'\033[{cursor_position}G')

        # Force flush the output
        sys.stdout.flush()

#-----------------------------------------------------------------------------

class cli:

    def __init__(self, app):
        self.app = app
        self.history = []
        self.hidx = 0
        self.cl = command(app)
        self.running = True
        self.prompt = '> '
        self.poll = None
        self.prompt_changed = False

    def set_root(self, root):
        """set the menu root"""
        self.root = root

    def set_prompt(self, prompt):
        """set the command prompt"""
        self.prompt = prompt
        self.prompt_changed = True

    def set_poll(self, poll):
        """set the external polling function"""
        self.poll = poll

    def func_help(self, help):
        """print help for a leaf function"""
        self.app.io.put('\n\n')
        for (parm, descr) in help:
            if parm != '':
                self.app.io.put('    %-19s: %s\n' % (parm, descr))
            else:
                self.app.io.put('    %-19s  %s\n' % ('', descr))

    def reset_history(self):
        """reset the command history index"""
        self.hidx = len(self.history)

    def add_history(self, cmd):
        """add a command to the history"""
        if cmd and (len(self.history) == 0 or self.history[-1] != cmd):
            self.history.append(cmd)
        self.reset_history()

    def put_history(self, cmd):
        """put a command into the history list"""
        n = len(self.history)
        if (n == 0) or ((n >= 1) and (self.history[-1] != cmd)):
            self.history.append(cmd)

    def get_history_rev(self):
        """get history in the reverse (up) direction"""
        n = len(self.history)
        if n != 0:
            if self.hidx > 0:
                # go backwards
                self.hidx -= 1
            else:
                # top of list
                self.app.io.put(chr(conio.CHAR_BELL))
            return self.history[self.hidx]
        else:
            # no history - return current command line
            return self.cl.get()

    def get_history_fwd(self):
        """get history in the forward (down) direction"""
        n = len(self.history)
        if self.hidx == n:
            # not in the history list - return current command line
            return self.cl.get()
        elif self.hidx == n - 1:
            # end of history recent - go back to an empty command
            self.hidx = n
            return ''
        else:
            # go forwards
            self.hidx += 1
            return self.history[self.hidx]

    def error_str(self, msg, cmds, idx):
        """return a parse error string"""
        marker = []
        for i in range(len(cmds)):
            l = len(cmds[i])
            if i == idx:
                marker.append('^' * l)
            else:
                marker.append(' ' * l)
        return '\n'.join([msg, ' '.join(cmds), ' '.join(marker)])

    def get_cmd(self):
        """
        accumulate input characters to the command line
        return True when processing is needed
        return False for on going input
        get a command from the user
        """
        self.cl.clear()
        self.cl.render()
        while True:
            c = self.app.io.get()
            if c is None:
                time.sleep(0.01)  # Add a small delay to prevent busy-waiting
                continue

            #print(f"\nDEBUG: Received char: {c}")  # Debugging print

            if c == conio.CHAR_CR:  # Enter key
                break
            elif c == conio.CHAR_BS:  # Backspace
                self.cl.backspace()
            elif c == conio.CHAR_DEL:  # Delete
                self.cl.delete()
            elif c == conio.CHAR_LEFT:  # Left arrow
                self.cl.left()
            elif c == conio.CHAR_RIGHT:  # Right arrow
                self.cl.right()
            elif c == conio.CHAR_HOME:  # Home
                self.cl.home()
            elif c == conio.CHAR_END:  # End
                self.cl.end()
            elif c == conio.CHAR_UP:  # Up arrow
                self.cl.set(self.get_history_rev()) # Set the command line to the previous history entry
            elif c == conio.CHAR_DOWN:  # Down arrow
                self.cl.set(self.get_history_fwd()) # Set the command line to the next history entry
            elif c >= 32 and c <= 126:  # Printable ASCII characters
                self.cl.add(chr(c))
            else:
                print(f"Unhandled character: {c}")

            self.cl.render()

        cmd = self.cl.get()
        return cmd

    def execute_cmd(self):
        """execute the command"""
        cmd = self.get_cmd()
        if cmd:
            self.add_history(cmd)
            self.app.put('\n')
            self.dispatch(cmd)
        else:
            print("No command received at execute_cmd")  # Debug print

    def dispatch(self, cmd):
        """dispatch the command to the appropriate handler"""
        parts = cmd.split()
        if not parts:
            return
        name = parts[0]
        args = parts[1:]
        print(f"Dispatching command: {name} with args: {args}")  # Debug print
        print(f"Available commands: {[cmd_name for cmd_name, _, _, _, _ in self.root]}")  # Debug print
        for (cmd_name, descr, help, leaf, submenu) in self.root:
            if cmd_name == name:
                if leaf:
                    print(f"Executing leaf function for command: {name}")  # Debug print
                    leaf(self.app, args)
                elif submenu:
                    print(f"Switching to submenu for command: {name}")  # Debug print
                    self.set_root(submenu)
                return
        self.app.put(f'Unknown command: {name}\n')
        print(f"Unknown command at dispatch: {name}")  # Debug print

    def parse_cmd(self):
        """
        parse and process the current command line
        return True if we need a new prompt line
        return False if we should reuse the existing one
        """
        # scan the command line into a list of tokens
        cmd_list = [cmd for cmd in self.cl.get().split(' ') if cmd != '']

        # if there are no commands, print a new empty prompt
        if len(cmd_list) == 0:
            self.cl.clear()
            return True

        # trace each command through the menu tree
        menu = self.root
        for idx in range(len(cmd_list)):
            cmd = cmd_list[idx]

            # A trailing '?' means the user wants help for this command
            if cmd[-1] == '?':
                # strip off the '?'
                cmd = cmd[:-1]
                # print the matching items and help strings for this menu
                self.app.io.put('\n\n')
                for (name, descr, help, leaf, submenu) in menu:
                    if name.startswith(cmd):
                        self.app.io.put('    %-19s: %s\n' % (name, descr))
                # strip off the '?' and recycle the command
                self.cl.erase()
                self.cl.repeat()
                return True

            # A trailing tab means the user wants command completion
            if cmd[-1] == '\t':
                # get rid of the tab
                cmd = cmd[:-1]
                self.cl.erase()
                matches = []
                for item in menu:
                    if item[0].startswith(cmd):
                        matches.append(item)
                if len(matches) == 0:
                    # no completions
                    self.app.io.put(chr(conio.CHAR_BELL))
                    return False
                elif len(matches) == 1:
                    # one completion: add it to the command
                    self.cl.add(matches[0][0][len(cmd):] + ' ')
                    self.cl.end()
                    return False
                else:
                    # multiple completions: display them
                    self.app.io.put('\n\n')
                    for (name, descr, help, leaf, submenu) in matches:
                        self.app.io.put('%s ' % name)
                    self.app.io.put('\n')
                    # recycle the command
                    self.cl.repeat()
                    return True

            # try to match the cmd with a unique menu item
            matches = []
            for item in menu:
                if item[0] == cmd:
                    # accept an exact match
                    matches = [item]
                    break;
                if item[0].startswith(cmd):
                    matches.append(item)
            if len(matches) == 0:
                # no matches - unknown command
                self.app.io.put('\n\n%s\n' % self.error_str('unknown command', cmd_list, idx))
                self.cl.repeat()
                return True
            if len(matches) == 1:
                # one match - submenu/leaf
                (name, descr, help, leaf, submenu) = matches[0]
                if submenu != None:
                    # switch to the submenu - continue parsing
                    menu = submenu
                    continue
                else:
                    # process leaf function - get the arguments
                    args = cmd_list[idx:]
                    del args[0]
                    if len(args) != 0:
                        if args[-1][-1] == '?':
                            # display help for the leaf function
                            self.func_help(help)
                            # strip off the '?', repeat the command
                            self.cl.erase()
                            self.cl.repeat()
                            return True
                        elif args[-1][-1] == '\t':
                            # tab happy user: strip off the tab
                            self.cl.erase()
                            self.cl.end()
                            return False
                    # call the leaf function
                    self.put_history(self.cl.get())
                    leaf(self.app, args)
                    self.cl.clear()
                    return True
            else:
                # multiple matches - ambiguous command
                self.app.io.put('\n\n%s\n' % self.error_str('ambiguous command', cmd_list, idx))
                self.cl.clear()
                return True

        # reached the end of the command list with no errors and no leaf function.
        self.app.io.put('\n\nadditional input needed\n')
        self.cl.repeat()
        return True

    def run(self):
        """run the CLI"""
        while self.running:
            if self.poll:
                self.poll()
            self.execute_cmd()
            if self.prompt_changed: # Check the flag
                self.cl.render()  # Re-render the prompt
                self.prompt_changed = False # Reset the flag

    def exit(self):
        """exit the cli"""
        self.running = False

#-----------------------------------------------------------------------------
