import time
from threading import Thread
import tkinter as tk
import turtle
import uuid
from math import pi, cos, sin, radians, degrees

class Playground:
    def __init__(self, width, height, title) -> None:
        self.root = tk.Tk()
        self.root.geometry("%ix%i" % (width, height))
        self.root.title(title)
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(self.root, width=width, height=height)
        self.canvas.pack(expand=True, fill=tk.BOTH)
        self.canvas.xview_moveto(.5)
        self.canvas.yview_moveto(.5)
        self.screen = turtle.TurtleScreen(self.canvas)
        self.screen.tracer(1, 0)
        self.fps = 400
        self.ips = 30
        self.interval = 1 / self.fps
        self.image_interval = 1 / self.ips
        self.last_update = None
        self.last_image_update = None
        self.bots = []
        self.end = False
        self.scale = 1.04 # In pixels / mm
        self.schedules = []
        rw = width  / self.scale
        rh = height / self.scale
        self.rect = (-rw/2, -rh/2, rw/2, rh/2) # Rectangle in mm (x1, y1, x2, y2)

    def register_bot(self, bot):
        self.bots.append(bot)

    def update(self):
        if self.last_update is None:
            self.last_update = time.perf_counter()
            self.last_image_update = self.last_update
            return

        current_time = time.perf_counter()
        delta_time = current_time - self.last_update
        self.last_update = current_time

        for bot in self.bots:
            bot.update(delta_time)

        for schedule in self.schedules:
            schedule()
        self.schedules.clear()

        if current_time - self.last_image_update > self.image_interval:
            self.screen.update()

    def mainloop(self):
        try:
            while not self.end:
                start = time.perf_counter()
                self.update()
                end = time.perf_counter()
                wait = self.interval - (end - start)
                if wait > 0:
                    time.sleep(wait)
                start = end
        except turtle.Terminator:
            pass
        except Exception as e:
            if not isinstance(e, tk.TclError):
                raise e

    def run_once(self, func):
        self.schedules.append(func)




class Bot:
    def __init__(self, playground: Playground, name: str = "Bot") -> None:
        self.playground = playground
        self.scale = playground.scale

        self.name = name
        self.shape = None
        self.turtle = turtle.RawTurtle(self.playground.screen)
        self.turtle.speed(0) # No speed limit

        self.x = 0
        self.y = 0
        self.heading = 0

        self.shape_name = str(uuid.uuid4())

        self.turtle.tiltangle(0)

        self.playground.register_bot(self)

        self.user_thread: Thread = None

    def run(self, func):
        if self.user_thread is None:
            self.user_thread = Thread(target=func, args=[self])
            self.user_thread.start()

    def teleport(self, x, y):
        self.x = x
        self.y = y
        self.turtle.up()
        self.turtle.setposition(self.x, self.y)
        self.turtle.down()

    def build_shape():
        pass # Child class must override this if needed

    def update_shape(self):
        self.build_shape()
        if self.shape is not None:
            self.playground.screen.addshape(self.shape_name, self.shape)
            self.turtle.shape(self.shape_name)
        self.teleport(self.x, self.y) # Teleport because pen offset may have changed

    def update(self, delta_time: float):
        pass # Child class must override this if needed



class TwoWheelsBot(Bot):
    def __init__(self, playground: Playground, name: str = "Bot") -> None:
        super().__init__(playground, name)

        # User configurable shape parameters (in mm)
        self.wheel_diameter = 66.5
        self.body_width = 150
        self.body_length = 200
        self.wheel_width = 25
        self.pen_offset = 100

        # User configurable colors
        self.body_color = "gainsboro"
        self.wheel_color = "crimson"
        self.head_color = "blue violet"
        self.pen_color = "medium blue"
        self.edges_color = "lime green"

        self.wheel_height = self.wheel_diameter
        self.wheels_distance = self.body_width - self.wheel_width

        self.update_shape()

    def teleport(self, x, y):
        self.x = x * 10
        self.y = y * 10
        new_x = (self.x + sin(self.heading) * self.pen_offset) * self.scale
        new_y = (self.y - cos(self.heading) * self.pen_offset) * self.scale
        self.turtle.up()
        self.turtle.setposition(new_x, new_y)
        self.turtle.down()

    def build_shape(self):
        self.shape = turtle.Shape("compound")

        body_left   = -(self.body_width / 2 + self.pen_offset) * self.scale
        body_right  =  (self.body_width / 2 - self.pen_offset) * self.scale
        body_top    =  (self.body_length / 2) * self.scale
        body_bottom = -(self.body_length / 2) * self.scale

        wheel_top    =  (self.wheel_height / 2) * self.scale
        wheel_bottom = -(self.wheel_height / 2) * self.scale
        wheel_width = self.wheel_width * self.scale

        self.shape.addcomponent((
            (body_left, body_top),
            (body_left, body_bottom),
            (body_right, body_bottom),
            (body_right, body_top)),
            self.body_color, self.edges_color) # Body

        self.shape.addcomponent((
            (body_left, wheel_top),
            (body_left, wheel_bottom),
            (body_left + wheel_width, wheel_bottom),
            (body_left + wheel_width, wheel_top)),
            self.wheel_color, self.wheel_color) # Left wheel

        self.shape.addcomponent((
            (body_right, wheel_top),
            (body_right, wheel_bottom),
            (body_right - wheel_width, wheel_bottom),
            (body_right - wheel_width, wheel_top)),
            self.wheel_color, self.wheel_color) # Right wheel

        self.shape.addcomponent((
            (body_left, body_top),
            (body_left, body_top - 2),
            (body_right, body_top - 2),
            (body_right, body_top)),
            self.head_color, self.head_color) # Head

        self.shape.addcomponent(((-1,-1), (1,-1), (1,1), (-1,1)), self.pen_color, self.pen_color) # Pen

    def update(self, delta_time: float):
        pass # Child class must override this if needed

    # Simulate wheel rotation of left and right wheel in degrees
    def add_wheel_delta(self, left_delta, right_delta):
        """
        vright = speed of right wheel
        vleft  = speed of left wheel
        dw = distance between wheels
        a = heading
        x, y = position

        a' = (vright - vleft) / dw * t + a
        k = (vright - vleft) / dw
        a' = k * t + a

        dx = cos(a') * (vright + vleft) * dt / 2
        dy = sin(a') * (vright + vleft) * dt / 2

        s = (vright + vleft) / 2
        x' = primitive( cos(k * t + a) * s * dt ) + x
        y' = primitive( sin(k * t + a) * s * dt ) + y

        x' = ( sin(k * t + a) / k + C_x) * s + x
        y' = (-cos(k * t + a) / k + C_y) * s + y

        C_x = -sin(a)
        C_y =  cos(a)
        """

        k = ((right_delta - left_delta) * pi * self.wheel_diameter / 360) / self.wheels_distance
        s = ((right_delta + left_delta) * pi * self.wheel_diameter / 360) / 2

        heading = self.heading

        if k != 0:
            self.x += ( sin(k + heading) - sin(heading)) / k * s
            self.y += (-cos(k + heading) + cos(heading)) / k * s
        else:
            self.x += cos(heading) * s
            self.y += sin(heading) * s
        new_heading = heading + k

        new_x = (self.x + sin(new_heading) * self.pen_offset) * self.scale
        new_y = (self.y - cos(new_heading) * self.pen_offset) * self.scale

        self.turtle.setposition(new_x, new_y)
        self.heading = new_heading
        self.turtle.setheading(degrees(new_heading))
