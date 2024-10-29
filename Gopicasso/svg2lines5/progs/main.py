#coding=utf-8
import os
parent_dir = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(__file__), "shapes")))
import sys
sys.path.insert(0, parent_dir)
from led_dance import *

import placementNoAsserv
led_timing(30)
import airplane
led_dance()
