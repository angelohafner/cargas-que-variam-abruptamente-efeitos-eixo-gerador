"""Generate label-free vector circuit symbols with the upstream Schemdraw core."""
from pathlib import Path
import sys
import math

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE/'vendor'))
import schemdraw
import schemdraw.elements as elm
from schemdraw.segments import Segment


def converter_symbol(width=1.2, height=1.0):
    """AC at the top bus, DC at the bottom battery; no flow direction implied."""
    converter = elm.Element().theta(0)
    paths = [
        [(-.6,-.5),(.6,-.5),(.6,.5),(-.6,.5),(-.6,-.5)],
        [(-.6,-.5),(.6,.5)],
        [(-.45+.40*i/64, .24+.085*math.sin(2*math.pi*i/64)) for i in range(65)],
        [(.08,-.18),(.46,-.18)],
    ]
    # Explicit dashes stay visible when the SVG is imported by Manim.
    for left in [.08,.23,.38]:
        paths.append([(left,-.31),(left+.08,-.31)])
    converter.segments.extend(
        Segment([(x*width/1.2,y*height) for x,y in path]) for path in paths
    )
    return converter


def generate():
    out = HERE/'assets'
    out.mkdir(exist_ok=True)
    schemdraw.use('svg')
    for name, element in [('generator', elm.SourceSin().right().length(2)),
                          ('battery', elm.Battery().up().length(2)),
                          ('load', elm.ResistorIEC().right().length(2)),
                          ('motor', elm.Motor().right().length(2))]:
        with schemdraw.Drawing(show=False, color='#F1F5FA', lw=2.5) as drawing:
            drawing += element
        drawing.save(str(out/(name+'.svg')))
    with schemdraw.Drawing(show=False, color='#F1F5FA', lw=2.5) as drawing:
        drawing += converter_symbol().at((0,0))
    drawing.save(str(out/'converter.svg'))
    # Complete single-line resource; animation assembles the same SVG symbols.
    with schemdraw.Drawing(show=False, color='#F1F5FA', lw=2.5) as drawing:
        drawing += elm.SourceSin().at((-5,0)).right().length(2)
        drawing += elm.Line().to((0,0))
        drawing += elm.Dot()
        drawing += elm.Line().to((3,0))
        drawing += elm.ResistorIEC().right().length(2)
        drawing += elm.Line().at((0,0)).to((0,-1))
        drawing += converter_symbol(width=1.0).at((0,-1.5))
        drawing += elm.Battery().at((0,-3.5)).up().length(1.5)
    drawing.save(str(out/'parallel_single_line.svg'))
    print('Schemdraw', schemdraw.__version__, ': vector assets ready')


if __name__ == '__main__':
    generate()
