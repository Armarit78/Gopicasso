from graph import *
import tkinter as tk


def _draw_bezier(canvas: tk.Canvas, p1, p2, p3, p4, fg: str="black", segments: int = 6, min_segment_length: float = 4):
    x, y = p1.x, p1.y
    segment_length = 0
    for i in range(1, segments + 1):
        t = i / segments
        a = (1 - t)**3
        b = 3 * (1 - t)**2 * t
        c = 3 * (1 - t) * t**2
        d = t**3
        nx = a * p1.x + b * p2.x + c * p3.x + d * p4.x
        ny = a * p1.y + b * p2.y + c * p3.y + d * p4.y
        segment_length += ((x-nx)**2 + (y-ny)**2) ** .5
        if segment_length < min_segment_length: continue
        segment_length = 0
        canvas.create_line(x, y, nx, ny, fill=fg)
        x, y = nx, ny


def draw_graph(graph: Graph, fg: str = "black", bg: str = "white", padding: float = 10, inverse_y: bool = False):
    root = tk.Tk()
    root.title("Graph")
    canvas = tk.Canvas(root, bg=bg)
    canvas.pack(fill=tk.BOTH, expand=True)

    minp, maxp = graph.get_bounding_box()

    canvas.update()
    w, h = canvas.winfo_width(), canvas.winfo_height()
    w -= padding * 2
    h -= padding * 2
    if inverse_y: h = -h
    #print("Size : (%f, %f)" % (w, h))

    x_scale = w / (maxp.x - minp.x)
    y_scale = h / (maxp.y - minp.y)
    if abs(x_scale) < abs(y_scale):
        y_scale = abs(x_scale) if y_scale > 0 else -abs(x_scale)
    else:
        x_scale = abs(y_scale) if x_scale > 0 else -abs(y_scale)

    x_offset = padding + abs(w) / 2 - (minp.x + (maxp.x - minp.x) / 2) * x_scale
    y_offset = padding + abs(h) / 2 - (minp.y + (maxp.y - minp.y) / 2) * y_scale

    for seg in graph.segments:
        for line in seg.lines:
            p1 = line.src    .clone().scale(x_scale, y_scale).offset(x_offset, y_offset)
            p2 = line.src_bzr.clone().scale(x_scale, y_scale).offset(x_offset, y_offset)
            p3 = line.dst_bzr.clone().scale(x_scale, y_scale).offset(x_offset, y_offset)
            p4 = line.dst    .clone().scale(x_scale, y_scale).offset(x_offset, y_offset)
            _draw_bezier(canvas, p1, p2, p3, p4, fg)

    root.mainloop()
