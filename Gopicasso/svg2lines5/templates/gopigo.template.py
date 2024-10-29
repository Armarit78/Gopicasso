#coding=utf-8

import os
parent_dir = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
print("Parent : %s" % parent_dir)

import sys
sys.path.insert(0, parent_dir)

import easygopigo3
from asserv import *


gpg = easygopigo3.EasyGoPiGo3()

asserv = Asserv(gpg)

gpg.set_speed(240)


#@body
