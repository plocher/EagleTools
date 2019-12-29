#!/usr/bin/env python3

"""
Author: John Plocher, 2019
URL:    www.SPCoast.com
License: Python Software Foundation License
"""

__version__ = "0.1"

# from CAMTool.fab.SiteConfiguration import * # local config details
from CAMTool.fab import CHMTPickNPlace

from xml.dom.minidom import parse
import xml.dom.minidom
import re

"""
sort based on alphanumeric order
   LED1 LED2 ... LED9 LED10...
"""
def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, s)]

"""
Read a .eaglerc file and extract the layer information (profile, id, color) from it
Profile 0, 1 and 2 are for the black, white an color background pallets
"""
def getLayers(eaglercfile):
    #                        Palette.0.0 = "0xFF000000"
    pattern = re.compile(r"""Palette                # opening tag
                         \.(?P<profile>\d)          # profile number
                         \.(?P<item>.*?)            # item number
                         \s*=\s*                    # whitespace = ...
                         "0x(?P<color>[0-9A-Fa-f]+) # hex alpha + RGB color
                         """, re.VERBOSE)
    palettes = {}
    with open(eaglercfile, 'r') as rcfile:
        for line in rcfile:
            match = pattern.match(line)
            if match:
                profile = int(match.group("profile"))
                item    = int(match.group("item"))
                color   = match.group("color")
                if profile not in palettes:
                    palettes[profile] = {}
                palettes[profile][item] = color
    return palettes

"""
Load the EAGLE CAD XML board file, generating dict's of
    * packages (name, smd/pth, x & y boundary)
    * layers (number, color)
    as well as the DOM (for further exploration by caller)
"""
def loadBoard(boardname, palettes):
    packages = {}

    # Open XML document using minidom parser
    DOMTree = xml.dom.minidom.parse(boardname)
    X = DOMTree.documentElement

    for P in X.getElementsByTagName("package"):
        me = {}
        me["name"] = P.getAttribute("name")
        me["smd"] = False   # default
        smd = P.getElementsByTagName("smd")
        if (smd):
            me["smd"] = True
        (me["xmin"], me["ymin"], me["xmax"], me["ymax"]) = getSymbolBounds(P,10000,10000,-10000,-10000)
        packages[me["name"].lower()] = me
        # print "Loaded: {} - bounds: ({},{}) ({},{})".format(me['name'],me["xmin"], me["ymin"], me["xmax"], me["ymax"])

    # <layers>
    # <layer number="1" name="Top" color="4" fill="1" visible="yes" active="yes"/>

    layers = {}
    for L in X.getElementsByTagName("layers"):
        for l in L.getElementsByTagName("layer"):
            lnum  = int(l.getAttribute("number"))
            litem = int(l.getAttribute("color"))
            #print("Layer[{}] = palettes[{}][{}] = {}".format(lnum, 0, litem, palettes[0][litem]))
            layers[lnum] = palettes[1][litem]
    return (X, packages, layers)

def loadLibrary(libname):
    packages = {}
    symbols  = {}


    # Open XML document using minidom parser
    DOMTree = xml.dom.minidom.parse(libname)
    X = DOMTree.documentElement

    for P in X.getElementsByTagName("package"):
        me = {}
        me["name"]        = P.getAttribute("name")
        me["description"] = ''
        D = P.getElementsByTagName("description")
        if D:
            me["description"] = " ".join(t.nodeValue for t in D[0].childNodes if t.nodeType == t.TEXT_NODE)
        me["description"] = me["description"].replace('\n', '<br>')
        me["smd"] = False   # default
        smd = P.getElementsByTagName("smd")
        if (smd):
            me["smd"] = True
        (me["xmin"], me["ymin"], me["xmax"], me["ymax"]) = getSymbolBounds(P,10000,10000,-10000,-10000)
        packages[me["name"].lower()] = me
        print("Package: {}: {} - bounds: ({},{}) ({},{})".format(me['name'],me['description'], me["xmin"], me["ymin"], me["xmax"], me["ymax"]))

        #for node in P.childNodes:
            #print("\tChild: {}".format(node.nodeName)

    return (X, packages, symbols)


def getSymbolBounds(E, xmin, ymin, xmax, ymax):
    for wire in E.getElementsByTagName("wire"):
        #if wire.getAttribute("layer") == "20":
        (xmin, ymin, xmax, ymax) = getElementBounds(wire, xmin, ymin, xmax, ymax)
    return (xmin, ymin, xmax, ymax)

def getElementBounds(E, xmin,ymin,xmax,ymax):
    wx1 = float(E.getAttribute("x1"))
    wy1 = float(E.getAttribute("y1"))
    wx2 = float(E.getAttribute("x2"))
    wy2 = float(E.getAttribute("y2"))
    if (wx1 > xmax): xmax = wx1
    if (wy1 > ymax): ymax = wy1
    if (wx1 < xmin): xmin = wx1
    if (wy1 < ymin): ymin = wy1
    if (wx2 > xmax): xmax = wx2
    if (wy2 > ymax): ymax = wy2
    if (wx2 < xmin): xmin = wx2
    if (wy2 < ymin): ymin = wy2
    return (xmin, ymin, xmax, ymax)

"""
My boards all have a special SYMBOL called "BOARD" that defines the DIM layer bounds.

I generally do not use individual 'lines on the DIM layer, instead I have defined many 
PACKAGES for the board SYMBOL, 
    e.g., 5cmx5cm, 10x10, 10x10 with rounded corners, 10x10 rounded with mounting holes, etc.
I can easily change the size of a board under design (change package...) if needed, and
with a common set of board footprints, I know the sizes for PCB fabrication, and more 
importantly, that all my jigs and test fixtures will work with the design.

This routine looks for a BOARD, and if found, uses its dimensions.
If one is not found, fall back to looking for wires on layer 20.
otherwise, return 0

"""
def getBoardDimensions(eagleBoard):
    xmax = -100000.0
    xmin = 100000.0
    ymax = xmax
    ymin = xmin

    for P in eagleBoard.getElementsByTagName("package"):
        name = P.getAttribute("name")
        if name.startswith('BOARD'):
            (xmin, ymin, xmax, ymax) = getSymbolBounds(P, xmin, ymin, xmax, ymax)
    if xmax > -100000.0:
        return (xmin,ymin,xmax,ymax)

    # no BOARD found, or no layer="20" wires on it, look for <board>'s layer20
    for P in eagleBoard.getElementsByTagName("board"):
        (xmin, ymin, xmax, ymax) = getSymbolBounds(P, xmin, ymin, xmax, ymax)

    if xmax > -100000.0:
        return (xmin, ymin, xmax, ymax)

    # no dimensions found...
    return (0,0,0,0)

"""
SMD Parts generally have no plated PADS
Only SMD Parts are pick-n-placed automatically
This returns a dict of SMD parts used in a design.
"""
def getSMDParts(eagleBoard, packages, component, feeder):
    parts = {}

    Boards = eagleBoard.getElementsByTagName("board")
    for B in Boards:
        # Get all the elements in the collection
        E = B.getElementsByTagName("element")

        # Print detail of each element.
        for e in E:
            if not e.hasAttribute("name"):
                continue
            # <element name="LED1" library="SPCoast" package="0603-LED" value="R" x="19.05" y="38.1" smashed="yes" rot="R180">

            me = {}
            me['name']    = e.getAttribute("name")
            me['library'] = e.getAttribute("library")
            me['package'] = e.getAttribute("package")
            me['value']   = e.getAttribute("value")
            me['x']       = e.getAttribute("x")
            me['y']       = e.getAttribute("y")
            me['rot']     = e.getAttribute("rot")
            me['smashed'] = e.getAttribute("smashed")
            me['smd']     = True  # corrected later if not...
            me['feeder']  = CHMTPickNPlace.SKIP

            id = me['value'].lower() + "-" + me['package'].lower()
            me['id']      = id

            parts[me['name']] = me

            if (me['package'].lower() not in packages) or (not packages[me['package'].lower()]["smd"]):
                # not a SMD part...
                me['smd'] = False
                continue

            c = CHMTPickNPlace.getFeederForComponent(id, component)
            if c != CHMTPickNPlace.SKIP:
                me['feeder'] = c

                # Normalize rotation...
                # Most all Eagle FootPrints are correct but we have to subtract 90 because
                # the CHMT tapes are mounted 90 degrees from the board
                if me['rot'] == '':
                    me['rot'] = 'R0'
                if me['rot'].startswith('MR'):
                    angle = int(me['rot'].lstrip('MR')) # TODO: Do I need to +180 ?
                if me['rot'].startswith('R'):
                    angle = int(me['rot'].lstrip('R'))
                else:
                    angle = int(me['rot'])
                angle = angle - 90

                # However, some feeders/FPs are not horizontal (trays...)
                # so we correct on a component by component basis
                angle = angle + int(feeder[c][CHMTPickNPlace.rotation])
                if (angle > 180):
                    angle -= 360
                me['rot'] = angle

                #print "SMD: {name:<10} {id} feeder: {feed}".format(name= e.getAttribute("name"), id= id, feed=component[id])
            else:
                me['feeder'] = CHMTPickNPlace.NOTFOUND
                # print "Note: Could not find feeder for part {} (ret={})".format(id, c)
        return parts

"""
The feeder sheet can mark a component as "SKIP"
If a design's part doesn't have an assigned feeder, assume it isn't used.
"""
def getUsedComponents(parts, feeder):
    used = {}
    for p in sorted(parts.keys()):
        if parts[p]['feeder'] == CHMTPickNPlace.SKIP:
            continue
        if parts[p]['feeder'] == CHMTPickNPlace.NOTFOUND:
            continue
        pn = feeder[parts[p]['feeder']][CHMTPickNPlace.partname]
        if pn not in used:
            used[pn] = []
        used[pn].append(p)
    return used

1;
