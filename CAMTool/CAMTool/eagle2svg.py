#!/usr/bin/env python3
"""
Author: John Plocher, 2019
URL:    www.SPCoast.com
License: Python Software Foundation License

Take an Eagle BRD file and render it as a SVG

Limits:  Some Eagle part numbers (names with embedded commas) are illegal XML tag names and cause the xml parser to throw errors
"""

import configparser
from pkg_resources import Requirement, resource_filename
from CAMTool.fab import CHMTPickNPlace, EagleCAD
import CAMTool.fab.SiteConfiguration as config

import sys
import svgwrite
import os
import datetime
import argparse
import io

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

    output = io.StringIO()

    output.write(date)
    output.write(time)

    contents = output.getvalue()
    output.close()
    return contents

# list of symbols...
def outputStations(used, feeder, component):
    output = io.StringIO()
    stacknumber = 0
    output.write("Table,No.,ID,DeltX,DeltY,FeedRates,Note,Height,Speed,Status,SizeX,SizeY,HeightTake,DelayTake,nPullStripSpeed\n")
    for p,v in enumerate(used):
        f = feeder[CHMTPickNPlace.getFeederForComponent(v, component)]

        output.write("Station, "
              "{stack:d}, {fnum:d}, {fXoff:0.2f}, {fYoff:0.2f}, "
              "{pullDist:d}, {name}, {placeHeight:0.2f}, {placeSpeed:d}, "
              "{options:d}, "
              "{sizeX:0.2f}, {sizeY:0.2f}, "
              "{pickHeight:0.2f}, {pickDelay:0.2f}, {pullSpeed:d}\n".format(
            stack=stacknumber,
            fnum=int(f[CHMTPickNPlace.feedernum]),
            fXoff=float(f[CHMTPickNPlace.feederXoff]),
            fYoff=float(f[CHMTPickNPlace.feederYoff]),
            pullDist=int(f[CHMTPickNPlace.pulldist]),
            name=f[CHMTPickNPlace.partname],
            placeHeight=float(f[CHMTPickNPlace.placeheight]),
            placeSpeed=int(f[CHMTPickNPlace.placespeed]),
            options=f[CHMTPickNPlace.options],
            sizeX=float(f[CHMTPickNPlace.partsizeX]),
            sizeY=float(f[CHMTPickNPlace.partsizeY]),
            pickHeight=float(f[CHMTPickNPlace.pickheight]),
            pickDelay=float(f[CHMTPickNPlace.pickdelay]),
            pullSpeed=int(f[CHMTPickNPlace.pullspeed])))

        stacknumber = stacknumber + 1
    output.write("\n")
    contents = output.getvalue()
    output.close()
    return contents


# actual parts
def outputParts(feeder, parts):
    output = io.StringIO()
    #EComponent, 0, 1, 1, 17, 19.05, 38.10, 90.00, 0.50, 2, 0, LED1, R - 0603, 0.00
    count = 0
    output.write("Table, No., ID, PHead, STNo., DeltX, DeltY, Angle, Height, Skip, Speed, Explain, Note, Delay\n")
    for pn in sorted(iter(parts.keys()), key=EagleCAD.natural_sort_key):
        p = parts[pn]
        fnum = p['feeder']
        if fnum == CHMTPickNPlace.SKIP or fnum == CHMTPickNPlace.NOTFOUND:
            continue
        f = feeder[fnum]

        output.write("EComponent, "
              "{num:d}, {id:d}, {head:d}, {fnum:d}, "
              "{cX:0.2f}, {cY:0.2f}, {angle:0.2f}, {height:0.2f}, "
              "{skip:d}, {speed:d}, {name}, {note}, {dly:0.2f}\n".format(
            num=count, id=count+1, head=int(f[CHMTPickNPlace.head]), fnum=int(f[CHMTPickNPlace.feedernum]),
            cX=float(p['x']), cY=float(p['y']), angle=p['rot'], height=float(f[CHMTPickNPlace.pickheight]),
            skip=int(f[CHMTPickNPlace.options]),
            speed=int(f[CHMTPickNPlace.pullspeed]),
            name=p['name'],
            note=f[CHMTPickNPlace.partname],
            dly=float(f[CHMTPickNPlace.pickdelay])
        ))
        count = count + 1
    output.write("\n")
    output.write("\n")

    contents = output.getvalue()
    output.close()
    return contents



def main():
    """
    main() 

    usage: eagle2svg.py [-h] pcbfile [pcbfile ...]

    Create a CHMT pick-n-place job from an EAGLEcad PCB board file.

    positional arguments:
      pcbfile     an EAGLEcad .brd file to process

    optional arguments:
      -h, --help  show this help message and exit


    """

    cfile = os.path.expanduser(config.DefaultConfigFile)
    if not os.path.isfile(cfile):
        print("First time usage: Creating {} with default contents - edit and customize before using!".format(cfile))
        examplefn = resource_filename(Requirement.parse('CAMTool'),"CAMTool/EagleTools.cfg")
        configuration = configparser.ConfigParser()
        configuration.read(examplefn)        
        with open(cfile, 'wb') as configfile:
            configuration.write(configfile)
        sys.exit(0)
    
    configuration = configparser.ConfigParser()
    configuration.read(cfile)
    
    parser = argparse.ArgumentParser(description='Create a SVG rendering from an EAGLEcad PCB board file.',
                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('PCBfile', metavar='pcbfile', type=str, nargs='+',
            help='an EAGLEcad .brd file to process')
    parser.add_argument("--feederfile", help="csv file with feeder component assignments")
    parser.add_argument("--outdir",     help="output directory (default is ./<PCBfile>.brd.svg)")
    parser.add_argument("--download",   action="store_true", help="download a fresh feeder file from Google Sheets?")
    parser.add_argument("--key",        help="Google Sheets document access key")

    args = parser.parse_args()
    args.config = configuration
    
    feederfile = args.config.get('EagleTools', 'defaultfeederfile')
    if args.feederfile:
        feederfile = args.feederfile

    if (args.download):
        CHMTPickNPlace.downloadFeederFile(args, feederfile, args.key)

    (feeder, component) = CHMTPickNPlace.loadFeeders(feederfile)

    for f in args.PCBfile:
        if len(args.PCBfile) > 1:
            print("Processing {}\n".format(f))

        outfilename = os.path.splitext(os.path.basename(f))[0] + ".brd.svg"
        outdir = os.path.dirname(f)

        if args.outdir:
            if args.outdir == '@':
                outdir = args.config.get('EagleTools', 'defaultSVGdir')
            elif args.outdir == "-":
                pass
            else:
                outdir = args.outdir
                
        bn = os.path.basename(outfilename)
        outfilename = os.path.join(outdir, bn)

        palettes = EagleCAD.getLayers("/Users/jplocher/.eaglerc")
        (eagleBoard, packages, layers) = EagleCAD.loadBoard(f, palettes)
        parts    = EagleCAD.getSMDParts(eagleBoard, packages, component, feeder)
        used     = EagleCAD.getUsedComponents(parts, feeder)


        # get max board dimensions
        (x1,y1,x2,y2) = EagleCAD.getBoardDimensions(eagleBoard)

        #print("dimensions: (x1:{} y1:{}), (x2:{},y2:{})".format(x1,y1,x2,y2))

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
            (x1,y1, x2,y2) = EagleCAD.getSymbolBounds(P, 10000, 10000, -10000, -10000)
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
                # [S][M]Rnnn
                #
                #     S    sets the Spin flag, which disable keeping texts readable from the bottom or right side of the drawing (only available in a board context)
                #     M    sets the Mirror flag, which mirrors the object about the y-axis
                #     Rnnn sets the Rotation to the given value, which may be in the range 0.0...359.9 (at a resolution of 0.1 degrees) in a board context, or one of 0, 90, 180 or 270 in a schematic context (angles may be given as negative values, which will be converted to the corresponding positive value)
                #
                #     The key letters S, M and R may be given in upper- or lowercase, and there must be at least R followed by a number.
                #     If the Mirror flag is set in an element as well as in a text within the element's package, they cancel each other out. The same applies to the Spin flag.
                #     Examples:
                #
                #     R0      no rotation
                #     R90     rotated 90 counterclockwise
                #     R-90    rotated 90 clockwise (will be converted to 270)
                #     MR0     mirrored about the y-axis
                #     SR0     spin texts
                #     SMR33.3 rotated 33.3 counterclockwise, mirrored and spin texts

                if not r or r == '':
                    angle=0
                elif r.startswith('MSR'):
                    angle = int(r.lstrip('MSR'))  # TODO: Do I need to += 180?
                elif r.startswith('SMR'):
                    angle = int(r.lstrip('SMR'))  # TODO: Do I need to += 180?
                elif r.startswith('MR'):
                    angle = int(r.lstrip('MR'))   # TODO: Do I need to += 180?
                elif r.startswith('SR'):
                    angle = int(r.lstrip('SR'))   # TODO: Do I need to += 180?
                elif r.startswith('R'):
                    angle = int(r.lstrip('R'))
                else:
                    angle = int(r)

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

if __name__ == "__main__":
    main()

