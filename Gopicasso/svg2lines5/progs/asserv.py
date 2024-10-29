#coding=utf-8
from math import pi, cos, sin, atan2, degrees, radians, acos
import time


# Shape in cm
# https://github.com/DexterInd/GoPiGo3/blob/f74d41d19191ad5484836d20542fd5d62ac2d25e/Software/Python/gopigo3.py#L81
wheel_diameter = 6.65
wheels_distance = 11.7


# Pen position in cm
pen_offset = 10.5


# Utility functions
def vector_length(x, y):
    return (x*x + y*y) ** .5

def vector_normalize(x, y):
    k = 1 / vector_length(x, y)
    return x * k, y * k

def angle_diff(src, dst):
    delta = (dst - src) % (2*pi)
    if delta > pi:
        return delta - 2 * pi
    return delta


class Asserv:
    def __init__(self, bot):
        # Current pen position
        self.bot_x = 0
        self.bot_y = pen_offset
        self.real_x = 0
        self.real_y = 0
        self.real_heading = 0

        # Current pen target (were it should be)
        self.target_x = 0
        self.target_y = 0
        self.target_heading = 0

        self.angle_error_gap = pi / 90
        self.move_error_gap = 1

        self.bot = bot
        self.wheel_diameter = wheel_diameter
        self.wheels_distance = wheels_distance
        self.pen_offset = pen_offset

        left_encoder, right_encoder = self.bot.read_encoders()
        self. left_encoder_offset = - left_encoder
        self.right_encoder_offset = -right_encoder

    def add_delta_encoders(self, left, right):
        delta_heading = ((right - left) * self.wheel_diameter * pi / 360) / self.wheels_distance
        delta_move    = ((right + left) * self.wheel_diameter * pi / 360) / 2

        if delta_heading != 0:
            self.bot_x += (sin(delta_heading + self.real_heading) - sin(self.real_heading)) * delta_move / delta_heading
            self.bot_y -= (cos(delta_heading + self.real_heading) - cos(self.real_heading)) * delta_move / delta_heading
        else:
            self.bot_x += cos(self.real_heading) * delta_move
            self.bot_y += sin(self.real_heading) * delta_move

        self.real_heading += delta_heading

        self.real_x = self.bot_x + sin(self.real_heading) * self.pen_offset
        self.real_y = self.bot_y - cos(self.real_heading) * self.pen_offset

        #print("Current pen position : %f %f" % (self.real_x, self.real_y))
        #bot = self.bot.BOT
        #x, y = self.real_x * 10 * bot.scale, -self.real_y * 10 * bot.scale
        #bot.playground.run_once(lambda: bot.playground.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill="red"))

    def check_encoders(self):
        left_encoder, right_encoder = self.bot.read_encoders()
        self.add_delta_encoders(left_encoder + self.left_encoder_offset, right_encoder + self.right_encoder_offset)
        self. left_encoder_offset = - left_encoder
        self.right_encoder_offset = -right_encoder

    def forward(self, d):
        self.target_x += cos(self.target_heading) * d
        self.target_y += sin(self.target_heading) * d
        self.go_to_target()

    def rotate(self, angle):
        self.target_heading = (self.target_heading + radians(angle)) % (2*pi)
        self.head_toward_target()

    def go_to_target(self, smooth=False):
        delta_x = self.target_x - self.real_x
        delta_y = self.target_y - self.real_y
        delta_move = vector_length(delta_x, delta_y)
        if delta_move < self.move_error_gap: return
        delta_heading = angle_diff(self.real_heading, -atan2(-delta_y, delta_x))

        if not smooth:
            self.raw_orbit(degrees(delta_heading))
            self.raw_forward(delta_move)
        else:
            if abs(delta_heading) < self.angle_error_gap:
                self.raw_forward(delta_move)
            else:
                self.raw_orbit(degrees(delta_heading * 2), (delta_move / 2) / cos(pi / 2 - abs(delta_heading)))

    def head_toward_target(self):
        delta_angle = angle_diff(self.real_heading, self.target_heading)
        if abs(delta_angle) < self.angle_error_gap: return
        self.raw_orbit(degrees(delta_angle))

    def raw_orbit(self, angle, radius = 0):
        self.check_encoders()

        if angle > 0:
            radius -= self.pen_offset
        elif angle < 0:
            radius += self.pen_offset

        if radius < 0:
            speed = self.bot.get_speed()
            self.bot.set_speed(-speed)
            self.bot.orbit(angle, -radius)
            self.bot.set_speed(speed)
        else:
            self.bot.orbit(-angle, radius)

        self.check_encoders()

    def raw_steer(self, left_percent, right_percent, speed_conservation=0):
        self.check_encoders()

        """
        left_percent / (R+c) = right_percent / R
        left_percent / right_percent = (R+c) / R = 1 + c / R
        R = c / (left_percent / right_percent - 1)

        left / (R' + d) = right / R'
        left / right = (R' + d) / R' = 1 + d / R'
        R' = d / (left / right - 1)
        R' = R + c / 2 + pen_offset - d / 2

        k = (left_percent - right_percent) / c
        left = k * (pen_offset + d/2 + c/2)
        right = k * (pen_offset - d/2 + c/2)
        """

        #print("Raw steer by %f %f" % (left_percent, right_percent))

        k = (left_percent - right_percent) / self.wheels_distance
        left = k * (self.pen_offset + self.wheels_distance) + right_percent
        right = k * (self.pen_offset) + right_percent

        k = 1 + speed_conservation * (self.pen_offset - 1)
        left  /= k
        right /= k

        maxv = max(abs(left), abs(right), 100) / 100

        self.bot.steer(left / maxv, right / maxv)

    def stop(self):
        self.check_encoders()
        self.bot.stop()
        self.check_encoders()

    def raw_forward(self, delta):
        self.check_encoders()
        self.bot.drive_cm(delta)
        self.check_encoders()

    def go_to(self, x, y, smooth=False):
        self.target_x = x
        self.target_y = y
        #print("Goto %f %f" % (x, y))
        self.go_to_target(smooth)

    def head_toward(self, angle):
        self.target_heading = radians(angle)
        self.head_toward_target()



def get_bezier_point(x1, y1, x2, y2, bx1, by1, bx2, by2, t):
    one_less_t = 1 - t
    a = one_less_t**3
    b = 3 * one_less_t**2 * t
    c = 3 * one_less_t * t**2
    d = t**3
    x = a * x1 + b * bx1 + c * bx2 + d * x2
    y = a * y1 + b * by1 + c * by2 + d * y2
    return x, y

def get_bezier_derivative(x1, y1, x2, y2, bx1, by1, bx2, by2, t):
    one_less_t = 1 - t
    a = 3 * one_less_t**2
    b = 6 * one_less_t * t
    c = 3 * t**2
    dx = a * (bx1 - x1) + b * (bx2 - bx1) + c * (x2 - bx2)
    dy = a * (by1 - y1) + b * (by2 - by1) + c * (y2 - by2)
    if dx == 0 and dy == 0:
        dt = 0.001
        p1 = get_bezier_point(x1, y1, x2, y2, bx1, by1, bx2, by2, t)
        p2 = get_bezier_point(x1, y1, x2, y2, bx1, by1, bx2, by2, t + dt)
        dx = (p2[0] - p1[0]) / dt
        dy = (p2[1] - p1[1]) / dt
    return dx, dy

def get_bezier_second_derivative(x1, y1, x2, y2, bx1, by1, bx2, by2, t):
    a = 6 * (1 - t)
    b = 6 * t
    sx = a * (bx2 - 2*bx1 + x1) + b * (bx1 - 2*bx2 + x2)
    sy = a * (by2 - 2*by1 + y1) + b * (by1 - 2*by2 + y2)
    return sx, sy



def follow_bezier_smooth(asserv, x1, y1, x2, y2, bx1, by1, bx2, by2, segments = 48, min_segment_length = 1.2):
    if vector_length(x1-x2, y1-y2) < 0.1: return

    segment_length = 0

    # Compute bezier points
    points = [(x1, y1)]
    px, py = x1, y1
    for i in range(1, segments + 1):
        t = i / segments
        nx, ny = get_bezier_point(x1, y1, x2, y2, bx1, by1, bx2, by2, t)

        segment_length += ((px-nx)**2 + (py-ny)**2) ** .5
        if segment_length < min_segment_length: continue
        segment_length = 0

        points.append((nx, ny))
        px, py = nx, ny

    points.append(get_bezier_point(x1, y1, x2, y2, bx1, by1, bx2, by2, 1.01))

    nx, ny = points[1]

    for i in range(len(points) - 2):
        rx, ry = asserv.real_x, asserv.real_y
        nx, ny = points[i + 1]
        mx, my = points[i + 2]

        seg1_angle = -atan2(-(ny - ry), (nx - rx))
        seg2_angle = -atan2(-(my - ny), (mx - nx))

        mina = angle_diff(seg2_angle, seg1_angle)
        maxa = angle_diff(seg1_angle, seg2_angle)
        if mina > maxa: mina, maxa = maxa, mina
        target_heading = min(max(angle_diff(seg1_angle, asserv.real_heading), mina), maxa) + seg1_angle

        if abs(angle_diff(asserv.real_heading, target_heading)) > pi / 20:
            asserv.head_toward(degrees(target_heading))

        asserv.go_to(nx, ny, smooth=True)


def follow_bezier_smart_smooth(asserv, x1, y1, x2, y2, bx1, by1, bx2, by2, segments = 48, min_angle = pi/16):
    if vector_length(x1-x2, y1-y2) < 0.1: return

    points = [(x1, y1)]
    px, py = get_bezier_derivative(x1, y1, x2, y2, bx1, by1, bx2, by2, 0)
    for i in range(1, segments):
        t = i / segments
        nx, ny = get_bezier_point(x1, y1, x2, y2, bx1, by1, bx2, by2, t)
        dx, dy = get_bezier_derivative(x1, y1, x2, y2, bx1, by1, bx2, by2, t)

        scalar = px * dx + py * dy
        cos_angle = scalar / (vector_length(dx, dy) * vector_length(px, py))
        angle = acos(min(max(cos_angle, -1), 1))
        if angle < min_angle: continue

        points.append((nx, ny))
        px, py = dx, dy

    points.append((x2, y2))
    dx, dy = vector_normalize(*get_bezier_derivative(x1, y1, x2, y2, bx1, by1, bx2, by2, 0.99))
    points.append((x2 + dx, y2 + dy))

    nx, ny = points[1]

    for i in range(len(points) - 2):
        rx, ry = asserv.real_x, asserv.real_y
        nx, ny = points[i + 1]
        mx, my = points[i + 2]

        seg1_angle = -atan2(-(ny - ry), (nx - rx))
        seg2_angle = -atan2(-(my - ny), (mx - nx))

        mina = angle_diff(seg2_angle, seg1_angle)
        maxa = angle_diff(seg1_angle, seg2_angle)
        if mina > maxa: mina, maxa = maxa, mina
        target_heading = min(max(angle_diff(seg1_angle, asserv.real_heading), mina), maxa) + seg1_angle

        if abs(angle_diff(asserv.real_heading, target_heading)) > pi / 20:
            asserv.head_toward(degrees(target_heading))

        asserv.go_to(nx, ny, smooth=True)


def get_nearest_on_segment(px, py, x1, y1, x2, y2):
    dy = y2 - y1
    dx = x2 - x1

    if dy == 0:
        return min(max((px - x1) / dx, 0), 1)
    if dx == 0:
        return min(max((py - y1) / dy, 0), 1)

    """
    k = -dx / dy
    c = py - px * k

    a(t) = (t * dx + x1, t * dy + y1)
    b(x) = (x, k * x + c)

    x = t * dx + x1
    k * x + c = t * dy + y1
    =>
    k * (t * dx + x1) + c = t * dy + y1
    =>
    k * x1 + c - y1 = t * dy - k * t * dx
    =>
    t = (k * x1 + c - y1) / (dy - k * dx)
    """

    k = -dx / dy
    c = py - px * k
    t = (k * x1 + c - y1) / (dy - k * dx)
    return min(max(t, 0), 1)


def follow_bezier_contiguous(asserv, x1, y1, x2, y2, bx1, by1, bx2, by2, segments = 64, interval = 0.08):
    if vector_length(x1-x2, y1-y2) < 0.1: return

    dx, dy = get_bezier_derivative(x1, y1, x2, y2, bx1, by1, bx2, by2, 0)
    angle = -atan2(-dy, dx)
    if abs(angle_diff(asserv.real_heading, angle)) > pi / 8:
        asserv.head_toward(degrees(angle))

    points = [(x1, y1)]
    for i in range(1, segments):
        t = i / segments
        points.append(get_bezier_point(x1, y1, x2, y2, bx1, by1, bx2, by2, t))
    points.append((x2, y2))

    last_t = 0
    first = True

    while True:
        rx, ry = asserv.real_x, asserv.real_y

        nearest_t = float('nan')
        nearest_distance = float('inf')
        nearest_point = None
        for i in range(len(points) - 1):
            dx, dy = get_bezier_derivative(x1, y1, x2, y2, bx1, by1, bx2, by2, (i+1) / segments)
            angle = -atan2(-dy, dx)
            d = ((points[i+1][0]-rx)**2 + (points[i+1][1]-ry)**2)**.5 + abs(angle_diff(asserv.real_heading, angle)) / pi * 5
            if d < 1:
                nearest_distance = d
                nearest_point = points[i+1]
                nearest_t = (i+1) / segments
                continue

            t = get_nearest_on_segment(rx, ry, points[i][0], points[i][0], points[i+1][0], points[i+1][1]) + i / segments
            p = get_bezier_point(x1, y1, x2, y2, bx1, by1, bx2, by2, t)
            dx, dy = get_bezier_derivative(x1, y1, x2, y2, bx1, by1, bx2, by2, t)
            angle = -atan2(-dy, dx)
            d = ((p[0]-rx)**2 + (p[1]-ry)**2)**.5
            d += abs(angle_diff(asserv.real_heading, angle)) / pi * 5

            if d < 0.8:
                d = nearest_distance
                t = (i+1) / segments

            if d <= nearest_distance:
                nearest_distance = d
                nearest_point = p
                nearest_t = t

        if nearest_t < last_t:
            nearest_t = last_t
            nearest_point = get_bezier_point(x1, y1, x2, y2, bx1, by1, bx2, by2, nearest_t)
            nearest_distance = ((nearest_point[0]-rx)**2 + (nearest_point[1]-ry)**2)**.5

        if nearest_t > 0.96: break

        last_t = nearest_t

        """
        dx, dy = get_bezier_derivative(...)
        dx', dy' = get_bezier_second_derivative(...)
        angle = -atan2(-dy, dx) = -atan(-dy/dx) = -atan(k) with k = -dy/dx
        k' = -(dy' * dx - dy * dx') / (dx^2)
        angular_speed = angle' = -k' / (1 + k^2)
        u(t) = (t - nearest_t) / (1 - nearest_t)
        u'(t) = 1 / (1 - nearest_t)
        point = bezier(t) + u(t) * (ox, oy)
        point' = bezier'(t) + u'(t) * (ox, oy)
        """
        ox, oy = rx - nearest_point[0], ry - nearest_point[1]
        dx, dy = get_bezier_derivative(x1, y1, x2, y2, bx1, by1, bx2, by2, nearest_t)
        dx -= ox / (1 - nearest_t)
        dy -= oy / (1 - nearest_t)
        sx, sy = get_bezier_second_derivative(x1, y1, x2, y2, bx1, by1, bx2, by2, nearest_t)
        if dx != 0:
            k = -dy / dx
            dk = -(sy * dx - dy * sx) / (dx*dx)
            angle = -atan2(-dy, dx)
            angular_speed = -dk / (1 + k*k) # (sy * dx - dy * sx) / (dx^2 - dy^2)
        else:
            angle = pi / 2 if dy > 0 else -pi / 2
            angular_speed = (sy * dx - dy * sx) / (dx**2 - dy**2)

        #if abs(angle_diff(asserv.real_heading, angle)) > pi / 3:
        #   asserv.head_toward(degrees(angle))

        delta_t = 0.001
        p1, p2 = nearest_point, get_bezier_point(x1, y1, x2, y2, bx1, by1, bx2, by2, nearest_t + delta_t)
        delta_d = ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)**.5
        angular_speed /= (delta_d / delta_t)

        delta_angle = angle_diff(asserv.real_heading, angle)
        angular_speed += delta_angle * 1.2
        #print("angular_speed = %f" % angular_speed)

        diff = angular_speed * asserv.wheels_distance / 2
        right = 1 + diff
        left  = 1 - diff
        maxv = max(abs(right), abs(left)) / 100

        if not first: time.sleep(interval)
        else: first = False

        asserv.raw_steer(left / maxv, right / maxv)

    asserv.stop()


def follow_bezier_no_bezier(asserv, x1, y1, x2, y2, bx1, by1, bx2, by2):
    asserv.go_to(x2, y2)


def follow_bezier_straight(asserv, x1, y1, x2, y2, bx1, by1, bx2, by2, segments = 6, min_segment_length = 3):
    if vector_length(x1-x2, y1-y2) < 0.1: return
    segment_length = 0
    px, py = x1, y1
    for i in range(1, segments):
        t = i / segments
        nx, ny = get_bezier_point(x1, y1, x2, y2, bx1, by1, bx2, by2, t)

        segment_length += ((px-nx)**2 + (py-ny)**2) ** .5
        if segment_length < min_segment_length: continue
        segment_length = 0

        asserv.go_to(nx, ny)
        px, py = nx, ny

    asserv.go_to(x2, y2)


def follow_bezier_smart_straight(asserv, x1, y1, x2, y2, bx1, by1, bx2, by2, segments = 6, min_angle = pi/6):
    if vector_length(x1-x2, y1-y2) < 0.1: return
    px, py = get_bezier_derivative(x1, y1, x2, y2, bx1, by1, bx2, by2, 0)
    for i in range(1, segments):
        t = i / segments
        dx, dy = get_bezier_derivative(x1, y1, x2, y2, bx1, by1, bx2, by2, t)

        scalar = px * dx + py * dy
        cos_angle = scalar / (vector_length(dx, dy) * vector_length(px, py))
        angle = acos(min(max(cos_angle, -1), 1))
        if angle < min_angle: continue

        asserv.go_to(*get_bezier_point(x1, y1, x2, y2, bx1, by1, bx2, by2, t))
        px, py = dx, dy

    asserv.go_to(x2, y2)

#most secure > worst secure
#follow_bezier_no_bezier>follow_bezier_straight>follow_bezier_smart_straight>follow_bezier_smooth>follow_bezier_smart_smooth>follow_bezier_contiguous

follow_bezier = follow_bezier_smart_smooth
