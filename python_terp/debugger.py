from pymetaterp.util import Node
import traceback

class Debugger:
    def __init__(self):
        self.waitlen = None
        self.printing = True
        self.line_printing = True
        self.command_buffer = ""

    def callback(self, terp, returned=None, return_value=None, func_name=None):
        stack = terp.stack
        frame = stack[-1]
        node = frame.root
        name = getattr(node, "name", type(node))
        step = frame.step
        if self.printing:
            print " " * len(stack), name, step,
            if returned:
                print "-->", repr(return_value)[:30]
            elif name == "NAME":
                print node[0]
            else:
                if name == "__call__":
                    print func_name
                print str(frame.outputs[-1])[:20] if frame.outputs else ""
        if self.line_printing:
            terp.stack_trace([terp.stack[-1]])
        if self.waitlen is not None and len(stack) > self.waitlen:
            return
        while True:
            if self.command_buffer:
                command, self.command_buffer = self.command_buffer[0], self.command_buffer[1:]
            else:
                command = raw_input("(dbg) ").strip()
            if command == "pdb":
                import pdb
                pdb.set_trace()
            elif command == "n":
                self.waitlen = len(stack)
                return
            elif command == "r":
                self.waitlen = len(stack) - 1
                return
            elif command == "c":
                self.waitlen = 0
                return
            elif command == "s":
                self.waitlen = None
                return
            elif command == "l":
                terp.stack_trace()
            elif command.startswith("b "):
                self.command_buffer = eval(command[2:])
            elif command == "p":
                print " " * len(stack), name,
                if returned:
                    print "-->", repr(return_value)[:30]
                elif name == "NAME":
                    print node[0]
                else:
                    print str(frame.outputs[-1])[:20] if frame.outputs else ""
            elif command == "!":
                old_waitlen = self.waitlen
                saved = terp.stack, terp.last_stack, terp.call_stack
                self.waitlen = 0
                terp.repl()
                terp.stack, terp.last_stack, terp.call_stack = saved
                stack = terp.stack
                self.waitlen = old_waitlen
            else:
                try:
                    co = compile(command, "<debug>", "single")
                    exec co in globals(), locals()
                except:
                    traceback.print_exc()
