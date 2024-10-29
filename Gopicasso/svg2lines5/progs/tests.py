#coding=utf-8

import easygopigo3
from time import sleep
from asserv import *


gpg = easygopigo3.EasyGoPiGo3()
asserv = Asserv(gpg)


gpg.set_speed(340)

#asserv.raw_steer(100, 100)
#sleep(1)
#asserv.raw_steer(-50, 50)
#sleep(1)
#asserv.raw_steer(0, 100)
#sleep(1)
#asserv.raw_steer(100, 0)
#sleep(1)
#asserv.stop()

follow_bezier(asserv, 0, 0, -20, 0, 0, -30, 20, 40)

#asserv.forward(10)
#asserv.rotate(45)
#asserv.forward(10)
#asserv.rotate(45 + 90)
#asserv.forward(20)

#asserv.go_to(30, 20, True)

#asserv.go_to( 20,  20)
#asserv.go_to( 20, -20)
#asserv.go_to(-20, -20)
#asserv.go_to(-20,  20)

exit(0)

gpg.turn_degrees(45)
gpg.turn_degrees(-90)
gpg.drive_cm(10)
gpg.drive_cm(-20)
gpg.spin_left()
sleep(0.6)
gpg.spin_right()
sleep(0.6)
gpg.orbit(90, 12)
gpg.orbit(-90, 12)
gpg.forward()
sleep(1)
gpg.stop()
sleep(1)
gpg.steer(-20, 100)
sleep(2)
gpg.drive_cm(20)
gpg.steer(100, 40)
sleep(1)
gpg.stop()
