from src.emu import *
from src.bots.gopigo.gopigo import *


program_file = "progs/shapes/airplane.py"

"""
Possible issues:
    GoPiGoMotor::set_limits() work also with negative values and go backward with positive dps
    delta_heading in Asserv::add_delta_encoders() is too small and floating point division is fucked
"""

pg = Playground(800, 800, "Playground")

bot = GoPiGoBot(pg)
bot.pen_offset = 105.5 # In mm

bot.teleport(0, 0)

pg.canvas.update()
w, h = pg.canvas.winfo_width(), pg.canvas.winfo_height()
print("Width = %f cm ; Height = %f cm" % (w/pg.scale/10, h/pg.scale/10))

import os
library_path = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(__file__), "src/bots/gopigo/libs")))
program_path = os.path.normpath(os.path.abspath(program_file))
program_dir  = os.path.dirname(program_path)

print("Library path : %s" % library_path)
print("Program path : %s" % program_path)
print()

os.chdir(os.path.dirname(program_dir))

import sys
sys.path.insert(0, program_dir)
sys.path.insert(0, library_path)

import builtins
builtins.EMULATED_BOT = bot

import importlib.util
spec = importlib.util.spec_from_file_location("__main__", program_path, submodule_search_locations=[program_dir])

def main(_):
    spec.loader.load_module()
    pg.run_once(lambda: bot.teleport(1000000, 0))

bot.run(main)

pg.mainloop()
