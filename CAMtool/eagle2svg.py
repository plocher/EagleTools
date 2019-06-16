#!/usr/bin/python
"""
Take an Eagle BRD file and render it as a SVG

  -John Plocher
   July 2018
   www.SPCoast.com

"""
from fab.SiteConfiguration import *

import svgwrite
import os
import datetime
import argparse
import StringIO
from fab import CHMTfeeders, EAGLEboard

"""
Output routines to create a SVG file

Note that there are several "typos" in the keywords used by the CHMT machine,
they are called out when found.

"""

STYLES = """.red { fill: red; stroke=none; }
.green { fill: green; stroke: none; }
.blue { fill: blue; stroke: yellow; stroke-width: 5; }
.yellow { fill: yellow; stroke: none; }
.text { font-family: serif; fill: white; }
"""


def u2mm(n):
    return n * 10000

def outputHeader(filename):
    now   = datetime.datetime.now()
    date  = now.strftime('DATE,%Y/%m/%d\n')
    time  = now.strftime('TIME,%H:%M:%S\n')
    fn    = os.path.splitext(os.path.basename(filename))[0]
    # File header

    output = StringIO.StringIO()

    output.write(date)
    output.write(time)

    contents = output.getvalue()
    output.close()
    return contents

# list of symbols...
def outputStations(used, feeder, component):
    output = StringIO.StringIO()
    stacknumber = 0
    output.write("Table,No.,ID,DeltX,DeltY,FeedRates,Note,Height,Speed,Status,SizeX,SizeY,HeightTake,DelayTake,nPullStripSpeed\n")
    for p,v in enumerate(used):
        f = feeder[CHMTfeeders.getFeederForComponent(v, component)]

        output.write("Station, "
              "{stack:d}, {fnum:d}, {fXoff:0.2f}, {fYoff:0.2f}, "
              "{pullDist:d}, {name}, {placeHeight:0.2f}, {placeSpeed:d}, "
              "{options:d}, "
              "{sizeX:0.2f}, {sizeY:0.2f}, "
              "{pickHeight:0.2f}, {pickDelay:0.2f}, {pullSpeed:d}\n".format(
            stack=stacknumber,
            fnum=int(f[CHMTfeeders.feedernum]),
            fXoff=float(f[CHMTfeeders.feederXoff]),
            fYoff=float(f[CHMTfeeders.feederYoff]),
            pullDist=int(f[CHMTfeeders.pulldist]),
            name=f[CHMTfeeders.partname],
            placeHeight=float(f[CHMTfeeders.placeheight]),
            placeSpeed=int(f[CHMTfeeders.placespeed]),
            options=f[CHMTfeeders.options],
            sizeX=float(f[CHMTfeeders.partsizeX]),
            sizeY=float(f[CHMTfeeders.partsizeY]),
            pickHeight=float(f[CHMTfeeders.pickheight]),
            pickDelay=float(f[CHMTfeeders.pickdelay]),
            pullSpeed=int(f[CHMTfeeders.pullspeed])))

        stacknumber = stacknumber + 1
    output.write("\n")
    contents = output.getvalue()
    output.close()
    return contents


# actual parts
def outputParts(parts):
    output = StringIO.StringIO()
    #EComponent, 0, 1, 1, 17, 19.05, 38.10, 90.00, 0.50, 2, 0, LED1, R - 0603, 0.00
    count = 0
    output.write("Table, No., ID, PHead, STNo., DeltX, DeltY, Angle, Height, Skip, Speed, Explain, Note, Delay\n")
    for pn in sorted(parts.iterkeys(), key=EAGLEboard.natural_sort_key):
        p = parts[pn]
        fnum = p['feeder']
        if fnum == CHMTfeeders.SKIP or fnum == CHMTfeeders.NOTFOUND:
            continue
        f = feeder[fnum]

        output.write("EComponent, "
              "{num:d}, {id:d}, {head:d}, {fnum:d}, "
              "{cX:0.2f}, {cY:0.2f}, {angle:0.2f}, {height:0.2f}, "
              "{skip:d}, {speed:d}, {name}, {note}, {dly:0.2f}\n".format(
            num=count, id=count+1, head=int(f[CHMTfeeders.head]), fnum=int(f[CHMTfeeders.feedernum]),
            cX=float(p['x']), cY=float(p['y']), angle=p['rot'], height=float(f[CHMTfeeders.pickheight]),
            skip=int(f[CHMTfeeders.options]),
            speed=int(f[CHMTfeeders.pullspeed]),
            name=p['name'],
            note=f[CHMTfeeders.partname],
            dly=float(f[CHMTfeeders.pickdelay])
        ))
        count = count + 1
    output.write("\n")
    output.write("\n")

    contents = output.getvalue()
    output.close()
    return contents




"""
main() 

usage: eagle2svg.py [-h] pcbfile [pcbfile ...]

Create a CHMT pick-n-place job from an EAGLEcad PCB board file.

positional arguments:
  pcbfile     an EAGLEcad .brd file to process

optional arguments:
  -h, --help  show this help message and exit


"""


parser = argparse.ArgumentParser(description='Create a SVG rendering from an EAGLEcad PCB board file.',
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('PCBfile', metavar='pcbfile', type=str, nargs='+',
                    help='an EAGLEcad .brd file to process')
parser.add_argument("--feederfile", help="csv file with feeder component assignments")
parser.add_argument("--outdir",     help="output directory (default is <PCBfile>.bom.txt)")
parser.add_argument("--download",   action="store_true", help="download a fresh feeder file from Google Sheets?")
parser.add_argument("--key",        help="Google Sheets document access key")

args = parser.parse_args()

feederfile = defaultfeederfile
if args.feederfile:
    feederfile = args.feederfile

if (args.download):
    CHMTfeeders.downloadFeederFile(feederfile, args.key)

(feeder, component) = CHMTfeeders.loadFeeders(feederfile)

for f in args.PCBfile:
    if len(args.PCBfile) > 1:
        print "Processing {}\n".format(f)

    outfilename = os.path.splitext(os.path.basename(f))[0] + ".svg"
    outdir = os.path.dirname(f)

    if args.outdir:
        if args.outdir == '@':
            outdir = defaultdir
        elif args.outdir == "-":
            pass
        else:
            outdir = args.outdir
        bn = os.path.basename(outfilename)

        outfilename = os.path.join(outdir, bn)

    palettes = EAGLEboard.getLayers("/Users/jplocher/.eaglerc")
    (eagleBoard, packages, layers) = EAGLEboard.loadBoard(f, palettes)
    parts    = EAGLEboard.getSMDParts(eagleBoard, packages, component, feeder)
    used     = EAGLEboard.getUsedComponents(parts, feeder)


    # get max board dimensions
    (x1,y1,x2,y2) = EAGLEboard.getBoardDimensions(eagleBoard)

    #print "dimensions: (x1:{} y1:{}), (x2:{},y2:{})".format(x1,y1,x2,y2)

    dwg = svgwrite.Drawing(outfilename, size=(x2-x1, y2-y1), debug=True)
    dwg.defs.add(dwg.style(STYLES))

    # Background will be dark but not black so the background does not overwhelm the colors.
    dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), fill='grey'))

    symbols = {}
    for P in eagleBoard.getElementsByTagName("package"):
        name = P.getAttribute("name").lower()
        # 1. create the symbol
        symbol = dwg.symbol(id=name)
        symbols[name] = symbol

        # 2. add symbols to the defs section
        dwg.defs.add(symbol)
        # 3. important: define viewbox of the symbol!
        (x1,y1, x2,y2) = EAGLEboard.getSymbolBounds(P, 10000, 10000, -10000, -10000)
        symbol.viewbox(x1,y1, x2,y2)
        # 4. add symbol to the container
        for wire in P.getElementsByTagName("wire"):
            layer = int(wire.getAttribute("layer"))
            width = float(wire.getAttribute("width"))
            if width == 0.0:
                width=1.0
            wx1 = float(wire.getAttribute("x1"))
            wy1 = float(wire.getAttribute("y1"))
            wx2 = float(wire.getAttribute("x2"))
            wy2 = float(wire.getAttribute("y2"))

            color_with_alpha = layers[layer]
            symbol.add(dwg.line((wx1, wy1), (wx2, wy2), stroke_width=width, stroke=svgwrite.rgb(
                int(color_with_alpha[2:4], 16),
                int(color_with_alpha[4:6], 16),
                int(color_with_alpha[6:8], 16))))

    for E in eagleBoard.getElementsByTagName("elements"):
        for e in E.getElementsByTagName("element"):
            # <element name="BOARD1" library="SPCoast" package="BOARD-SEEED10X10-NOHOLES" value="" x="0" y="0"/>
            # <element name="UPPER" library="SPCoast" package="1X04_LOCK" value="1x4 0.100" x="22.86" y="7.62" smashed="yes" rot="R180">
            # <attribute name="NAME" x="24.765" y="6.35" size="0.889" layer="25" font="vector" ratio="11" rot="R180"/>
            # </element>
            # <element name="LOWER" library="SPCoast" package="1X04_LOCK" value="1x4 0.100" x="22.86" y="3.81" smashed="yes" rot="R180">
            # <attribute name="NAME" x="24.749" y="1.222" size="0.889" layer="25" font="vector" ratio="11" rot="R180"/>
            # </element>
            # <element name="LED1" library="SPCoast" package="0603-LED" value="R" x="19.05" y="38.1" smashed="yes" rot="R180">
            # <attribute name="OPL" value="19-217-R6C-AL1M2VY-3T" x="19.05" y="38.1" size="1.778" layer="27" rot="R180" display="off"/>
            # <attribute name="VALUE" x="24.13" y="38.735" size="1.27" layer="27" rot="R180"/>
            # </element>
            name = e.getAttribute("name").lower()
            pkg  = e.getAttribute("package").lower()
            x    = float(e.getAttribute("x"))
            y    = float(e.getAttribute("y"))
            r    = e.getAttribute("rot")
            if not r or r == '':
                angle=0
            elif r.startswith('R'):
                angle = int(r.lstrip('R'))
            else:
                angle = int(r)
            """
            print("looking for {}...".format(pkg))
            print("packages[]={}".format(packages))
            print("packages[{}]={}".format(pkg, packages[pkg]))
            print symbols
            """
            # rot="rotate({} {} {})".format(180, x+(packages[pkg]['xmax'] - packages[pkg]['xmin'])/2, y+(packages[pkg]['ymax'] - packages[pkg]['ymin'])/2);
            rot="rotate({} {} {})".format(angle, x, y)
            dwg.add( dwg.use(symbols[pkg], transform=rot, insert=(x + packages[pkg]['xmin'], y + packages[pkg]['ymin']), size=(packages[pkg]['xmax'] - packages[pkg]['xmin'], packages[pkg]['ymax'] - packages[pkg]['ymin'])))

    for E in eagleBoard.getElementsByTagName("plain"):
        for wire in E.getElementsByTagName("wire"):
            layer = int(wire.getAttribute("layer"))
            width = float(wire.getAttribute("width"))
            if width == 0.0:
                width = 1.0
            wx1 = float(wire.getAttribute("x1"))
            wy1 = float(wire.getAttribute("y1"))
            wx2 = float(wire.getAttribute("x2"))
            wy2 = float(wire.getAttribute("y2"))

            color_with_alpha = layers[layer]
            dwg.add(dwg.line((wx1, wy1), (wx2, wy2), stroke_width=width, stroke=svgwrite.rgb(
                int(color_with_alpha[2:4], 16),
                int(color_with_alpha[4:6], 16),
                int(color_with_alpha[6:8], 16))))

    dwg.save()

