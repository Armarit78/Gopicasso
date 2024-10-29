from ...emu import *


class GoPiGoMotor:
    def __init__(self) -> None:
        self.encoder = 0
        self.limit = 0
        self.speed = 0
        self.target = None
        self.accel = 5400
        self.decel = 5800
        self.velocity = 0

    def _target_reached(self, precision: float = 2):
        return abs(self.encoder - self.target) <= precision

    def _update_velocity(self, desired_speed: float, delta_time: float):
        a = self.accel if abs(self.velocity) < abs(desired_speed) else self.decel
        if self.velocity < desired_speed:
            self.velocity = min(self.velocity + a * delta_time, desired_speed)
        elif self.velocity > desired_speed:
            self.velocity = max(self.velocity - a * delta_time, desired_speed)
        self.velocity = desired_speed

    # Update motor rotation and return delta degrees
    def update(self, delta_time: float) -> float:
        if self.target is None:
            desired_speed = min(max(self.speed, -self.limit), self.limit)
        elif not self._target_reached():
            desired_speed = self.limit * (1 if self.target > self.encoder else -1)
        else:
            desired_speed = 0
        self._update_velocity(desired_speed, delta_time)
        delta_rotate = self.velocity * delta_time
        self.encoder += delta_rotate
        return delta_rotate

    def set_position(self, degrees: float) -> None:
        self.target = degrees
        self.speed = 0

    def get_encoder(self) -> float:
        return int(self.encoder + 0.5)

    def set_limits(self, dps: float) -> None:
        if dps < 0: dps = -dps #print("Error (GoPiGoMotor.set_limits) : dps is negative")
        self.limit = dps

    def set_power(self, power: int) -> None:
        if power == -128:
            self.set_dps(0)
        else:
            self.set_dps(power / 127 * 500) # TODO : Don't hard code 500

    def set_dps(self, dps: float) -> None:
        self.target = None
        self.speed = dps

    def offset_encoder(self, degrees: float) -> None:
        self.encoder -= degrees


class GoPiGoBot(TwoWheelsBot):
    def __init__(self, playground: Playground, name: str = "GoPiGo Bot") -> None:
        super().__init__(playground, name)

        self.default_speed = 300 # In mm / seconds
        self.speed = self.default_speed

        self.wheels_distance = 117 # In mm
        self.wheel_diameter = 66.5 # In mm

        self. left_motor = GoPiGoMotor()
        self.right_motor = GoPiGoMotor()

        # Hardwares sensors
        self.distance_sensor = GoPiGoDistanceSensor(self)

        self.update_shape()

    def update(self, delta_time: float):
        self.add_wheel_delta(self.left_motor.update(delta_time), self.right_motor.update(delta_time))


class GoPiGoDistanceSensor:
    def __init__(self, bot: GoPiGoBot) -> None:
        self.bot = bot

    def read_mm(self) -> float:
        rect = self.bot.playground.rect
        segments = [
            (rect[0], rect[1], rect[2], rect[1]),
            (rect[2], rect[1], rect[2], rect[3]),
            (rect[2], rect[3], rect[0], rect[3]),
            (rect[0], rect[3], rect[0], rect[1])
        ]
        d = self.raytrace(self.bot.x, self.bot.y, cos(self.bot.heading), sin(self.bot.heading), segments)
        if d == float('inf'): return 8190
        return d

    def raytrace(self, x, y, dx, dy, segments):
        best_d = float('inf')
        for seg in segments:
            d = self.intersection(x, y, dx, dy, *seg)
            if d >= 0 and d < best_d:
                best_d = d
        return best_d

    def intersection(self, x, y, dx, dy, x1, y1, x2, y2):
        """
        a(k) = (x  + k *  dx,  y + k *  dy)
        b(t) = (x1 + t * idx, y1 + t * idy)

        x + k * dx = x1 + t * idx
        y + k * dy = y1 + t * idy

        k = (x1 + t * idx - x) / dx
        y + ((x1 + t * idx - x) / dx) * dy = y1 + t * idy

        y - y1 + (x1 - x) * (dy / dx) = t * idy - t * idx * (dy / dx)

        t = (y - y1 + (x1 - x) * (dy / dx)) / (idy - idx * (dy / dx))
        """
        idx = x2 - x1
        idy = y2 - y1

        if dx == 0:
            if idx == 0: return -1
            d = (x - x1) / idx * idy + y1 - y
            if dy < 0 and d < 0: return -d
            elif dy > 0 and d > 0: return d
            return -1

        a = (idy - idx * (dy / dx))
        if a == 0: return -1

        t = (y - y1 + (x1 - x) * (dy / dx)) / a
        k = (x1 + t * idx - x) / dx

        if k < 0 or t > 1 or t < 0: return -1

        ix, iy = t * idx + x1, t * idy + y1
        return ((ix - x)**2 + (iy - y)**2)**.5
