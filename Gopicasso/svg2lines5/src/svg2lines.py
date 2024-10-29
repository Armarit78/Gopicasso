import xml.etree.ElementTree as ET
import sys
import numpy as np
from .graph import *
from .minheap import *



def error(msg: str, code: int = 1) -> None:
    print("Error: " + msg, file=sys.stderr, flush=True)
    exit(code)



class Svg2LinesException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class Svg2LinesParser:
    def __init__(self) -> None:
        self.graph: Graph = Graph()
        self.offset: int = 0
        self.data: str = None
        self.one_line_per_path: bool = False

    def parse_path_skip_sep(self) -> None:
        m = len(self.data)
        while self.offset < m:
            c = self.data[self.offset]
            if c != ',' and not c.isspace():
                break
            self.offset += 1

    def parse_path_number(self) -> int:
        start = self.offset
        m = len(self.data)
        has_comma = False
        has_exp = False
        if self.offset >= m:
            raise Svg2LinesException("End of path data reached too early")
        if self.data[self.offset] == '-':
            self.offset += 1
        while self.offset < m:
            c = self.data[self.offset]
            if not has_comma and not has_exp and c == '.':
                has_comma = True
            elif not has_exp and c == 'e':
                has_exp = True
                if self.offset < m-1 and self.data[self.offset+1] == '-':
                    self.offset += 1
            elif not c.isdigit():
                break
            self.offset += 1
        s = self.data[start:self.offset]
        try:
            v = float(s)
            self.parse_path_skip_sep()
            return v
        except ValueError:
            raise Svg2LinesException("Invalid number found in path data '%s' after '%s'" % (s, self.data[max(0, self.start-24):self.start]))

    def parse_path(self, node: ET.Element) -> None:
        if "d" not in node.attrib:
            raise Svg2LinesException("A path element doesn't have a 'd' attribute")

        self.data = node.attrib["d"]
        self.offset = 0

        current_point = GraphPoint(0, 0)
        current_node = self.graph.new_node(current_point.clone())
        current_seg = current_node.new_segment()

        last_alpha = '@'

        has_line = False
        new_line = False
        last_bzr = Point()

        self.parse_path_skip_sep()

        m = len(self.data)
        while self.offset < m:
            c = self.data[self.offset]

            if not c.isalpha():
                c = last_alpha
            else:
                last_alpha = c
                self.offset += 1

            self.parse_path_skip_sep()

            if c == 'l':
                current_point.offset(self.parse_path_number(), self.parse_path_number())
                current_seg.new_line(current_point)
            elif c == 'L':
                current_point.set(self.parse_path_number(), self.parse_path_number())
                current_seg.new_line(current_point)
            elif c == 'm':
                current_point.offset(self.parse_path_number(), self.parse_path_number())
                new_line = True
            elif c == 'M':
                current_point.set(self.parse_path_number(), self.parse_path_number())
                new_line = True
            elif c == 'h':
                current_point.x += self.parse_path_number()
                current_seg.new_line(current_point)
            elif c == 'H':
                current_point.x = self.parse_path_number()
                current_seg.new_line(current_point)
            elif c == 'v':
                current_point.y += self.parse_path_number()
                current_seg.new_line(current_point)
            elif c == 'V':
                current_point.y = self.parse_path_number()
                current_seg.new_line(current_point)
            elif c == 'z' or c == 'Z':
                current_seg.end_to(current_node)
                current_seg = current_node.new_segment()
                current_point.copy(current_node.point)
            elif c == 'c':
                src_bzr = current_point.relative(self.parse_path_number(), self.parse_path_number())
                dst_bzr = current_point.relative(self.parse_path_number(), self.parse_path_number())
                current_point.offset(self.parse_path_number(), self.parse_path_number())
                current_seg.new_line(current_point, src_bzr, dst_bzr)
                last_bzr.copy(dst_bzr)
            elif c == 'C':
                src_bzr = Point(self.parse_path_number(), self.parse_path_number())
                dst_bzr = Point(self.parse_path_number(), self.parse_path_number())
                current_point.set(self.parse_path_number(), self.parse_path_number())
                current_seg.new_line(current_point, src_bzr, dst_bzr)
                last_bzr.copy(dst_bzr)
            elif c == 's':
                if last_bzr.is_nan(): last_bzr.copy(current_point)
                dst_bzr = current_point.relative(self.parse_path_number(), self.parse_path_number())
                current_point.offset(self.parse_path_number(), self.parse_path_number())
                current_seg.new_line(current_point, last_bzr.opposite(current_point), dst_bzr)
                last_bzr.copy(dst_bzr)
            elif c == 'S':
                if last_bzr.is_nan(): last_bzr.copy(current_point)
                dst_bzr = Point(self.parse_path_number(), self.parse_path_number())
                current_point.set(self.parse_path_number(), self.parse_path_number())
                current_seg.new_line(current_point, last_bzr.opposite(current_point), dst_bzr)
                last_bzr.copy(dst_bzr)
            elif c == 'q':
                bzr = current_point.relative(self.parse_path_number(), self.parse_path_number())
                current_point.offset(self.parse_path_number(), self.parse_path_number())
                current_seg.new_line(current_point, bzr, bzr)
                last_bzr.copy(bzr)
            elif c == 'Q':
                bzr = Point(self.parse_path_number(), self.parse_path_number())
                current_point.set(self.parse_path_number(), self.parse_path_number())
                current_seg.new_line(current_point, bzr, bzr)
                last_bzr.copy(bzr)
            elif c == 't':
                current_point.offset(self.parse_path_number(), self.parse_path_number())
                bzr = last_bzr.opposite(current_point)
                current_seg.new_line(current_point, bzr, bzr)
                last_bzr.copy(bzr)
            elif c == 'T':
                current_point.set(self.parse_path_number(), self.parse_path_number())
                bzr = last_bzr.opposite(current_point)
                current_seg.new_line(current_point, bzr, bzr)
                last_bzr.copy(bzr)
            elif c == 'a' or c == 'A':
                # TODO: See https://stackoverflow.com/questions/1734745/how-to-create-circle-with-b%C3%A9zier-curves
                raise Svg2LinesException("Circle are not yet supported as path operator")
            else:
                raise Svg2LinesException("Unknown path operator found '%s'" % c)

            if len(current_seg) > 0:
                has_line = True

            if new_line:
                if has_line and self.one_line_per_path: break
                if len(current_seg) == 0:
                    current_seg.remove()
                elif current_seg.end is None:
                    current_seg.create_end()
                if len(current_node.links) == 0:
                    current_node.point.copy(current_point)
                else:
                    current_node = self.graph.new_node(current_point.clone())
                current_seg = current_node.new_segment()
                new_line = False

            self.parse_path_skip_sep()

        if len(current_seg) == 0:
            current_seg.remove()
        elif current_seg.end is None:
            current_seg.create_end()


    def fix_tag(self, tag: str) -> str:
        pos = tag.rfind('}')
        return tag if pos == -1 else tag[pos+1:]

    def parse_node(self, node: ET.Element) -> None:
        tag = self.fix_tag(node.tag)
        if tag == "path":
            self.parse_path(node)
        else:
            for child in node:
                self.parse_node(child)

    def parse(self, root: ET.Element) -> None:
        if self.fix_tag(root.tag) != "svg":
            raise Svg2LinesException("The root element is not a SVG tag")
        self.parse_node(root)



# Links line together to make a graph and known what is the next line
def clean_graph(graph: Graph, link_radius: float = 0.1):
    pass # TODO


# https://gamedev.stackexchange.com/questions/5373/moving-ships-between-two-planets-along-a-bezier-missing-some-equations-for-acce/5427#5427
def bezier_length(line: GraphLine, segments: int = 6) -> float:
    pass # TODO
    return line.src.distance(line.dst)


# https://stackoverflow.com/questions/2742610/closest-point-on-a-cubic-bezier-curve#answer-57315396
# return the closest point to 'pt' and the 't' variable of the bezier equation
def bezier_closest_point(line: GraphLine, pt: Point) -> tuple[Point, float]:
    pass # TODO


"""
def _find_shortest_path(graph: Graph, point: GraphPoint, parents: np.ndarray, scores: np.ndarray):
    score = 0
    while True:
        candidats = []
        for next in point.links:
            if parents[next.index] == -1:
                candidats.append(next)

        if len(candidats) > 1:
            next_scores = []
            for next in candidats:
                parents[next.index] = point.index
                score = _find_shortest_path(graph, next, parents, scores)
                scores[next.index] = score
                next_scores.append(score)
                next_scores[-1] += point.distance(next)

        elif len(candidats) == 1:
            next = candidats[0]
            parents[next.index] = point.index
            score += point.distance(next) * 2
            point = next

        else:
            break
    return score


def find_shortest_path(graph: Graph, start: int):
    nb_points = len(graph.points)
    parents = np.array([-1] * nb_points, dtype=int)
    scores = np.array([-1] * nb_points, dtype=int)
    _find_shortest_path(graph, start, parents, scores)
"""


"""
     v
1 -- 2 -- 3 -- 4 -- 5
          |  /      |
          7 ------- 6

Etapes:
    Supposons que le point 2 est le point de départ
    Choisisons arbitrairement le prochain point, donc supposons que c'est 1:
    Vérifié si 1 est déja visité et s'il ne l'ai pas:
        Le point actuelle est mtn 1
        On note le point actuelle (1) comme étant visité
        Répété l'operation depuis 1 mais 1 n'a pas de liens pas encore visité donc cherché le chemain le plus coure vers 2
    A partir de 2 on tests un autre liens pas encore visité donc 3:
        Le point actuelle est maintenant 3
        On note le point actuelle (3) comme étant visité
        Répété l'opération depuis 3:
            Il y a deux liens pas encore visité (vers 4 et 7)
            Donc on choisi arbitrairement de commencé par 4:
                Le point actuelle est mainenant 4:
"""


def graph_find_segment(start: GraphNode, end: GraphNode) -> GraphSegment:
    for node, segment in start:
        if node == end:
            return segment
    return None


def graph_build_shortest_path(graph: Graph, start: GraphNode, end: GraphNode, parents: np.ndarray, visiteds: np.ndarray):
    path = []
    rpath = []
    length = 0
    nodes = graph.nodes

    current = end
    while True:
        index = parents[current.index]
        if index < 0: break
        parent = nodes[index]
        segment = graph_find_segment(parent, current)
        path.append((current, segment))
        rpath.append((parent, segment))
        length += segment.length
        current = parent
    path.reverse()

    current = start
    i = 0
    sublength = 0
    for node, segment in path:
        for _, seg in current.links:
            if seg != segment and not visiteds[seg.index]:
                p, back, back_len = graph_find_travel_rec(graph, current, visiteds)
                rp = rpath[-i:] if i > 0 else []
                return path[:i] + p, back + rp, back_len + length
        visiteds[segment.index] = True
        current = node
        i += 1
        sublength += segment.length

    return path, rpath, length


def graph_find_shortest(graph: Graph, start: GraphNode, end: GraphNode, visiteds: np.ndarray):
    heap = MinHeap()
    heap.push(0, start)

    parents = np.full(len(graph.nodes), -1, dtype=int)
    parents[start.index] = -2

    while heap.current_size > 0:
        distance, node = heap.pop()
        for next, segment in node.links:
            if parents[next.index] < 0: continue
            parents[next.index] = node.index
            if next == end:
                # Yeh we found a path!
                return graph_build_shortest_path(graph, end, parents, visiteds)
            length = segment.length if visiteds[segment.index] else 0
            heap.push(distance + length, next)

    # Failed to find a path
    return None


def graph_find_travel_rec(graph: Graph, current: GraphNode, visiteds: np.ndarray):
    issues = []

    for node, segment in current.links:
        if not visiteds[segment.graph_index]:
            visiteds[segment.graph_index] = True
            issues.append((*graph_find_travel_rec(graph, node, visiteds), node, segment))

    if len(issues) == 0:
        return [], [], 0.0

    # Sort issues by ascending order of cost of the path to come back,
    # so the longest one is the last
    issues.sort(key = lambda x: x[2])

    path = []
    for i in range(len(issues) - 1):
        issue = issues[i]
        path.append((issue[3], issue[4]))
        path.extend(issue[0])
        path.extend(issue[1])
        path.append((current, issue[4]))

    last_issue = issues[-1]

    path.append((last_issue[3], last_issue[4]))
    path.extend(last_issue[0])

    path_to_come_back: list = last_issue[1]
    cost_to_come_back: float = last_issue[2]

    path_to_come_back.append((current, last_issue[4]))
    cost_to_come_back += last_issue[4].length

    return path, path_to_come_back, cost_to_come_back


def graph_find_travel(graph: Graph, start: GraphNode):
    visiteds = np.zeros(len(graph.segments), dtype=bool)
    path, _, _ = graph_find_travel_rec(graph, start, visiteds)
    return path


def graph_link_groups(graph: Graph):
    nodes = graph.nodes
    nb_nodes = len(nodes)

    points = graph.points
    nb_points = len(points)

    # Detect groupes of points linked together
    nodes_groupe = np.zeros(nb_nodes, dtype=int)
    points_groupe = np.zeros(nb_points, dtype=int)
    groupes: list[list[GraphPoint]] = []
    queue: list[GraphNode] = []
    groupe_id = 1
    for i in range(nb_nodes):
        if nodes_groupe[i] != 0:
            continue
        queue.clear()
        queue.append(nodes[i])
        groupe = []
        groupes.append(groupe)
        while len(queue) > 0:
            point = queue.pop()
            if nodes_groupe[point.graph_index] != 0:
                continue
            nodes_groupe[point.graph_index] = groupe_id
            for next, seg in point.links:
                if nodes_groupe[next.graph_index] == 0:
                    queue.append(next)
                for p in seg.points:
                    if points_groupe[p.graph_index] == 0:
                        points_groupe[p.graph_index] == groupe_id
                        groupe.append(p)
        groupe_id += 1
    nb_groupes = len(groupes)

    inf = float('inf')

    # Find the shortest segment between each groups
    groupes_links = [[None for _ in range(nb_groupes)] for _ in range(nb_groupes)]
    for i in range(nb_groupes):
        for j in range(nb_groupes):
            if i == j: continue
            best_d = inf
            best_pair = None
            for point in groupes[i]:
                for other in groupes[j]:
                    d = point.distance(other)
                    if d < best_d:
                        best_d = d
                        best_pair = (point, other)
            groupes_links[i][j] = (best_d, best_pair)

    # Links groups in the best way
    linked_groups = [0]
    unlinked_groups = [i for i in range(1, nb_groupes)]
    while len(unlinked_groups) > 0:
        best_unlinked = None
        best_pair = None
        best_d = inf
        for a in unlinked_groups:
            for b in linked_groups:
                d, pair = groupes_links[a][b]
                if d < best_d:
                    best_d = d
                    best_pair = pair
                    best_unlinked = a
        if best_pair is None: break
        unlinked_groups.remove(best_unlinked)
        linked_groups.append(best_unlinked)
        best_pair[0].link(best_pair[1])


def graph_find_draw_path(graph: Graph, start_x: float, start_y: float):
    graph_link_groups(graph)

    # Find the nearest point to (start_x, start_y)
    shortest_d = float('inf')
    nearest_point = None
    start_p = GraphPoint(start_x, start_y)
    for point in graph.points:
        d = point.distance(start_p)
        if d < shortest_d:
            shortest_d = d
            nearest_point = point

    # Create a segment between start_p and the nearest node on the graph
    initial_node = graph.new_node(start_p)
    initial_node.point.link(nearest_point)

    # Find the shortest path to go through all links
    return graph_find_travel(graph, initial_node)
