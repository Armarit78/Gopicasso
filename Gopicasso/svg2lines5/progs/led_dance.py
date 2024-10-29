#coding=utf-8
import easygopigo3
import time
from math import sqrt
from random import randrange, random

FROM_COLOR = (0, 0xFF, 0)
TO_COLOR = (0xFF, 0, 0)

def lerp(a, b, t):
    return (1 - t) * a + t * b

def color_clamp(c):
    return (min(max(int(c[0]), 0), 0xFF), min(max(int(c[1]), 0), 0xFF), min(max(int(c[2]), 0), 0xFF))

def color_lerp(a, b, t):
    return color_clamp((lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)))

def color_random():
    return (randrange(256), randrange(256), randrange(256))

def color_maximize(c):
    k = 0xFF / max(c)
    return color_clamp((c[0] * k, c[1] * k, c[2] * k))

def color_random_teint():
    x = random() * 3
    if x < 1:
        c = color_lerp((0xFF, 0, 0), (0, 0xFF, 0), x)
    elif x < 2:
        c = color_lerp((0, 0xFF, 0), (0, 0, 0xFF), x - 1)
    else:
        c = color_lerp((0, 0, 0xFF), (0xFF, 0, 0), x - 2)
    return color_maximize(c)

def led_timing(t):
    gopigo = easygopigo3.EasyGoPiGo3()
    start = time.time()
    # temps initial de sommeil (en secondes)
    initial_sleep_time = (3 + sqrt(-319 + 80*t)) / 40 #étude de fonction afin d'obtenir cette fonction (CI : f(1) = 24, f(1.5) = 49, f(2) = 90  donc f(x)= 20x^2-3x+4 donc f-1(x)= cette fonction)
    sleep_time = initial_sleep_time

    # temps de réduction de sommeil (en secondes)
    sleep_time_reduction = 0.05

    # boucle pour faire clignoter la LED de plus en plus vite
    while True:
        t = 1 - (sleep_time / initial_sleep_time)

        gopigo.blinker_on('left')
        gopigo.blinker_on('right')
        gopigo.set_led(gopigo.LED_LEFT_EYE + gopigo.LED_RIGHT_EYE, 255)
        gopigo.set_eye_color(color_lerp(FROM_COLOR, TO_COLOR, t))
        gopigo.open_eyes()
        print('on')
        time.sleep(sleep_time)

        gopigo.blinker_off('left')
        gopigo.blinker_off('right')
        gopigo.set_led(gopigo.LED_LEFT_EYE + gopigo.LED_RIGHT_EYE, 0)
        gopigo.close_eyes()
        print('off')
        time.sleep(sleep_time)

        # s'assurer que la led clignotte vite quand elle s'approche de la fin du timer
        if sleep_time < 0.2:
            sleep_time -= sleep_time_reduction/4
        else:
            sleep_time -= sleep_time_reduction

        # s'assurer que le temps de sommeil ne devient pas négatif
        if sleep_time < 0:
            break

    print("temps total d'exec :", time.time() - start)

    # éteindre la LED à la fin de l'exécution
    gopigo.blinker_on('left')
    gopigo.blinker_on('right')
    gopigo.set_led(gopigo.LED_LEFT_EYE + gopigo.LED_RIGHT_EYE, 255)
    time.sleep(1)
    gopigo.blinker_off('left')
    gopigo.blinker_off('right')
    gopigo.set_led(gopigo.LED_LEFT_EYE + gopigo.LED_RIGHT_EYE, 0)


def led_dance():
    gopigo = easygopigo3.EasyGoPiGo3()
    try:
        while True:
            gopigo.set_left_eye_color(color_random_teint())
            gopigo.open_left_eye()
            time.sleep(0.4)
            gopigo.set_right_eye_color(color_random_teint())
            gopigo.open_right_eye()
            time.sleep(0.4)
    except KeyboardInterrupt:
        gopigo.close_eyes()

