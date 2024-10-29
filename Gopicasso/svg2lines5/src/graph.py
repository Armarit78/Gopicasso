NaN = float("nan")
Inf = float('inf')


class Point:
    def __init__(self, x: float = NaN, y: float = NaN) -> None:
        self.x = x
        self.y = y

    def __str__(self) -> str:
        return "(%.3f, %.3f)" % (self.x, self.y)

    def clone(self) -> 'Point':
        return Point(self.x, self.y)

    def relative(self, dx: float, dy: float) -> 'Point':
        return self.clone().offset(dx, dy)

    def offset(self, dx: float, dy: float) -> 'Point':
        self.x += dx
        self.y += dy
        return self

    def scale(self, sx: float, sy: float) -> 'Point':
        self.x *= sx
        self.y *= sy
        return self

    def set(self, x: float, y: float) -> 'Point':
        self.x = x
        self.y = y
        return self

    def opposite(self, center: 'Point' = None) -> 'Point':
        if center is None: center = Point(0, 0)
        return self.clone().scale(-1, -1).offset(center.x*2, center.y*2)

    def copy(self, other: 'Point') -> None:
        self.x = other.x
        self.y = other.y

    def distance(self, other) -> float:
        return ((self.x - other.x)**2 + (self.y - other.y)**2) ** .5

    def is_nan(self) -> bool:
        return self.x == NaN or self.y == NaN


class GraphPoint(Point):
    def __init__(self, x: float = NaN, y: float = NaN) -> None:
        super().__init__(x, y)
        self.intersection: bool = False
        self.parent: GraphNode | GraphSegment = None # A GraphNode if intersection is True or GraphSegment otherwise
        self.graph_index: int = -1
        self.seg_index: int = -1

    def clone(self) -> 'GraphPoint':
        return GraphPoint(self.x, self.y)

    def link(self, other: 'GraphPoint') -> 'GraphSegment':
        if other.intersection:
            other_node = other.parent
        else:
            other_node = other.parent.split(other.seg_index)

        if self.intersection:
            self_node = self.parent
        else:
            self_node = self.parent.split(self.seg_index)

        seg = self_node.new_segment()
        seg.end_to(other_node)

        return seg


class GraphLine:
    def __init__(self, src: GraphPoint, dst: GraphPoint,  src_bzr: Point = None, dst_bzr: Point = None) -> None:
        self.src: GraphPoint = src
        self.dst: GraphPoint = dst
        self.src_bzr: Point = src if src_bzr is None else src_bzr
        self.dst_bzr: Point = dst if dst_bzr is None else dst_bzr
        self.length: float = src.distance(dst)
        self.seg_index: int = -1
        self.segment = None

    def __str__(self) -> str:
        return "%s --> %s" % (str(self.src), str(self.dst))


class GraphSegment:
    def __init__(self) -> None:
        self.graph_index: int = -1
        self.lines: list[GraphLine] = []
        self.points: list[GraphPoint] = []
        self.length: int = 0
        self.start: GraphNode = None
        self.end: GraphNode = None
        self.graph: Graph = None

    def add_point(self, point: GraphPoint) -> None:
        if point.parent != self:
            point.parent = self
            point.intersection = False
            point.seg_index = len(self.points)
            self.points.append(point)
        self.graph.add_point(point)

    def add_line(self, line: GraphLine) -> None:
        if len(self.points) == 0:
            self.points.append(line.src)
        self.add_point(line.dst)
        line.seg_index = len(self.lines)
        line.segment = self
        line.seg_index = len(self.lines)
        self.lines.append(line)
        self.length += line.length

    def split(self, index: int) -> 'GraphNode':
        node = self.graph.new_node(self.points[index])
        seg = node.new_segment()
        for i in range(index, len(self.lines)):
            seg.add_line(self.lines[i])
        self.lines = self.lines[:index]
        self.graph.break_link_for(self.start, self)
        self.graph.break_link_for(self.end, self)
        seg.end = self.end
        seg.start = node
        self.end = node
        self.compute_length()
        seg.compute_length()
        node.link(seg.end, seg)
        self.start.link(node, self)
        return node

    def new_line(self, dst: Point, src_bzr: Point = None, dst_bzr: Point = None) -> GraphLine:
        last_point = self.points[-1] if len(self.points) > 0 else self.start.point
        point = GraphPoint(dst.x, dst.y)
        line = GraphLine(last_point, point, src_bzr, dst_bzr)
        self.graph.add_point(point)
        self.add_line(line)
        return line

    def end_to(self, other: 'GraphNode', src_bzr: Point = None, dst_bzr: Point = None) -> GraphLine:
        last_point = self.points[-1] if len(self.points) > 0 else self.start.point
        line = GraphLine(last_point, other.point, src_bzr, dst_bzr)
        self.add_line(line)
        self.end = other
        self.start.link(self.end, self)
        return line

    def create_end(self) -> 'GraphNode':
        end_point = self.lines[-1].dst
        self.end = self.graph.new_node(end_point)
        self.start.link(self.end, self)
        return self.end

    def remove(self) -> None:
        self.graph.remove_segment(self)

    def compute_length(self) -> None:
        self.length = 0
        for line in self.lines:
            self.length += line.length

    def __len__(self) -> int:
        return len(self.lines)

    def __getitem__(self, index) -> GraphLine:
        return self.lines[index]


class GraphNode:
    def __init__(self) -> None:
        self.graph_index: int = -1
        self.links: list[tuple[GraphNode, GraphSegment]] = []
        self.point: GraphPoint = None
        self.graph: Graph = None

    def link(self, other: 'GraphNode', segment: GraphSegment) -> None:
        segment.start = self
        segment.end = other
        self.links.append((other, segment))
        other.links.append((self, segment))
        self.graph.add_segment(segment)

    def new_segment(self) -> GraphSegment:
        seg = GraphSegment()
        seg.start = self
        self.graph.add_segment(seg)
        return seg


class Graph:
    def __init__(self) -> None:
        self.nodes: list[GraphNode] = []
        self.segments: list[GraphSegment] = []
        self.points: list[GraphPoint] = []

    def get_bounding_box(self) -> tuple[Point,Point]:
        min_x =  Inf
        min_y =  Inf
        max_x = -Inf
        max_y = -Inf
        for p in self.points:
            min_x = min(min_x, p.x)
            min_y = min(min_y, p.y)
            max_x = max(max_x, p.x)
            max_y = max(max_y, p.y)
        return Point(min_x, min_y), Point(max_x, max_y)

    def add_node(self, node: GraphNode) -> None:
        if node.graph == self: return
        node.graph = self
        node.graph_index = len(self.nodes)
        self.nodes.append(node)
        self.add_point(node.point)
        for next, seg in node.links:
            self.add_segment(seg)
            self.add_node(next)

    def has_node(self, node: GraphNode) -> bool:
        return 0 <= node.graph_index < len(self.nodes) and self.nodes[node.graph_index] == node

    def remove_node(self, node: GraphNode) -> None:
        if not self.has_node(node): return
        self.remove_point(node.point)
        for _, seg in node.links:
            self.remove_segment(seg)
        last_node = self.nodes.pop()
        if last_node != node:
            self.nodes[node.graph_index] = last_node
            last_node.graph_index = node.graph_index
        node.graph = None
        node.graph_index = -1

    def add_segment(self, seg: GraphSegment) -> None:
        if self.has_segment(seg): return
        seg.graph = self
        seg.graph_index = len(self.segments)
        self.segments.append(seg)
        for p in seg.points:
            self.add_point(p)

    def has_segment(self, seg: GraphSegment) -> bool:
        return 0 <= seg.graph_index < len(self.segments) and self.segments[seg.graph_index] == seg

    def remove_segment(self, seg: GraphSegment) -> None:
        if not self.has_segment(seg): return
        for p in seg.points:
            self.remove_point(p)
        last_seg = self.segments.pop()
        if last_seg != seg:
            self.segments[seg.graph_index] = last_seg
            last_seg.graph_index = seg.graph_index
        seg.graph = None
        seg.graph_index = -1
        self.break_link_for(seg.start, seg)
        self.break_link_for(seg.end, seg)

    def break_link_for(self, node: GraphNode, seg: GraphSegment):
        if node is None: return
        i = 0
        while i < len(node.links):
            s = node.links[i][1]
            if s == seg:
                last_link = node.links.pop()
                if i < len(node.links):
                    node.links[i] = last_link
            else:
                i += 1

    def add_point(self, point: GraphPoint) -> None:
        if self.has_point(point): return
        point.graph_index = len(self.points)
        self.points.append(point)

    def has_point(self, point: GraphPoint) -> bool:
        return 0 <= point.graph_index < len(self.points) and self.points[point.graph_index] == point

    def remove_point(self, point: GraphPoint) -> None:
        if not self.has_point(point): return
        last_point = self.points.pop()
        if last_point != point:
            self.points[point.graph_index] = last_point
            last_point.graph_index = point.graph_index
        last_point.graph_index = -1

    def new_node(self, point: GraphPoint) -> GraphNode:
        node = GraphNode()
        node.point = point
        point.intersection = True
        point.parent = node
        self.add_node(node)
        return node

    def resize(self, x: float, y: float, w: float, h: float, keep_aspect = True) -> None:
        minp, maxp = self.get_bounding_box()
        x_scale = w / (maxp.x - minp.x)
        y_scale = h / (maxp.y - minp.y)
        if keep_aspect:
            if abs(x_scale) < abs(y_scale):
                y_scale = abs(x_scale) if y_scale > 0 else -abs(x_scale)
            else:
                x_scale = abs(y_scale) if x_scale > 0 else -abs(y_scale)
        x_offset = x + abs(w) / 2 - (minp.x + (maxp.x - minp.x) / 2) * x_scale
        y_offset = y + abs(h) / 2 - (minp.y + (maxp.y - minp.y) / 2) * y_scale
        scaled_points = set()
        for seg in self.segments:
            for line in seg.lines:
                if line.src not in scaled_points:
                    line.src.scale(x_scale, y_scale).offset(x_offset, y_offset)
                    scaled_points.add(line.src)
                if line.dst not in scaled_points:
                    line.dst.scale(x_scale, y_scale).offset(x_offset, y_offset)
                    scaled_points.add(line.dst)
                if line.src_bzr not in scaled_points:
                    line.src_bzr.scale(x_scale, y_scale).offset(x_offset, y_offset)
                    scaled_points.add(line.src_bzr)
                if line.dst_bzr not in scaled_points:
                    line.dst_bzr.scale(x_scale, y_scale).offset(x_offset, y_offset)
                    scaled_points.add(line.dst_bzr)
