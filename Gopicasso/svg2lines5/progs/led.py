#coding=utf-8
import easygopigo3
import time
from math import sqrt

def led_timing(t):
    gopigo = easygopigo3.EasyGoPiGo3()
    start = time.time()
    # temps initial de sommeil (en secondes)
    sleep_time = (3 + sqrt(-319 + 80*t)) / 40 #étude de fonction afin d'obtenir cette fonction (CI : f(1) = 24, f(1.5) = 49, f(2) = 90  donc f(x)= 20x^2-3x+4 donc f-1(x)= cette fonction)

    # temps de réduction de sommeil (en secondes)
    sleep_time_reduction = 0.05

    # boucle pour faire clignoter la LED de plus en plus vite
    while True:
        gopigo.blinker_on('left')
        gopigo.blinker_on('right')
        gopigo.set_led(gopigo.LED_LEFT_EYE + gopigo.LED_RIGHT_EYE, 255)
        print('on')
        time.sleep(sleep_time)
        gopigo.blinker_off('left')
        gopigo.blinker_off('right')
        gopigo.set_led(gopigo.LED_LEFT_EYE + gopigo.LED_RIGHT_EYE, 0)
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

led_timing(40) #temps précis entre 10s et 100s (écart d'erreur entre temps indiqué et pratique < 5%)
