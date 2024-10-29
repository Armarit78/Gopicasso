from src.svg2lines import *
import os


def follow_path(path: list[tuple[GraphPoint, GraphSegment]], min_bezier_length = 2) -> str:
    out = ""
    for node, seg in path:
        if seg.end == node:
            for i in range(len(seg.lines)):
                line = seg.lines[i]
                p = line.dst
                out += "follow_bezier(asserv, %f, %f, %f, %f, %f, %f, %f, %f)\n" % (line.src.x, line.src.y, p.x, p.y, line.src_bzr.x, line.src_bzr.y, line.dst_bzr.x, line.dst_bzr.y)
        else:
            for i in range(len(seg.lines) - 1, -1, -1):
                line = seg.lines[i]
                p = line.src
                out += "follow_bezier(asserv, %f, %f, %f, %f, %f, %f, %f, %f)\n" % (line.dst.x, line.dst.y, p.x, p.y, line.dst_bzr.x, line.dst_bzr.y, line.src_bzr.x, line.src_bzr.y)
    return out


def generate(svg_filename: str, template_filename: str, output_filename: str, x, y, w, h) -> None:
    # Load SVG file
    root = None
    with open(svg_filename, 'r') as file:
        root = ET.parse(file).getroot()
    if root is None:
        error("Failed to load SVG file")

    # Parse SVG file
    parser = Svg2LinesParser()
    try:
        parser.parse(root)
    except Svg2LinesException as e:
        error(str(e))

    # Load template file
    template = None
    with open(template_filename, 'r') as file:
        template = file.read()
    if template is None:
        error("Failed to load template file")

    parser.graph.resize(x, y, w, -h) #carré de (-40:-40) à (40:40) les deux derniers argument sont la largeur et la hauteur

    body = follow_path(graph_find_draw_path(parser.graph, 0, 0))

    template = template.replace("#@body", body)

    # Write template
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    with open(output_filename, 'w') as file:
        file.write(template)


input_folder = "images"
output_folder = "progs/shapes"
template_filename = "templates/gopigo.template.py"


for filename in os.listdir(input_folder):
    svg_filename = os.path.join(input_folder, filename)
    output_filename = os.path.join(output_folder, os.path.splitext(filename)[0]  + ".py")
    print("Generate programe for '%s'" % filename)
    generate(svg_filename, template_filename, output_filename, -20, -20, 40, 40)
