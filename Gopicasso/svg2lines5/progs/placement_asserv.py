from easygopigo3 import EasyGoPiGo3
from asserv import *
import time

degrees_step = 10 # degrees
delta = 120 # mm

gpg = EasyGoPiGo3()

asserv = Asserv(gpg)
asserv.pen_offset = 0

gpg.set_speed(100) #on fait le robot aller lentement pour réduire les approximations de l'asservissement

my_distance_sensor = gpg.init_distance_sensor()

def Searching():
    L = []
    angle = 0
    while angle <= 360:
        distance = my_distance_sensor.read_mm()
        if distance >= 3000:
            distance = 0 #si distance = 3000 on l'a règle à 0.

        print("Distance : %f" % distance)
        L.append((distance, angle))

        asserv.rotate(degrees_step) #faire tourner le véhicule autour de lui d'un certain angle à chaque fois
        angle += degrees_step
        time.sleep(0.2)

    max_dist = 0
    angle_max_dist = 0
    for k in L:
        if k[0] > max_dist :
            max_dist = k[0]
            angle_max_dist = k[1]

    return max_dist, angle_max_dist

max_dist, angle_max_dist = Searching()
print(max_dist, angle_max_dist)

asserv.rotate(angle_max_dist)
asserv.forward((max_dist - delta) / 10)

max_dist, angle_max_dist = Searching()
print(max_dist, angle_max_dist)

asserv.rotate(angle_max_dist)
asserv.forward((max_dist-delta)/2 / 10)

asserv.head_toward(0)
