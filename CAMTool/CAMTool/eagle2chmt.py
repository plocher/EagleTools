#!/usr/bin/env python3

"""
Author: John Plocher, 2019
URL:    www.SPCoast.com
License: Python Software Foundation License

Inspired by Sparkfun's CHMT ULP tutorial
(https://www.sparkfun.com/sparkx/blog/2591)

This is a stand alone script that can be run from a Makefile without invoking eagle and running the ULP interactively
The Google Doc forat is expanded and reordered from the Sparkfun original - feel free to look at / borrow the one
referenced here with the default key


"""

import configparser
from pkg_resources import Requirement, resource_filename
import CAMTool.fab.SiteConfiguration as config
from .fab import CHMTPickNPlace, EagleCAD

import sys
import os
import datetime
import argparse
import io
import os.path


"""
Output routines to create a CharmHigh dpv file

Note that there are several "typos" in the keywords used by the CHMT machine,
they are called out when found.

"""

def outputHeader(filename):
    now   = datetime.datetime.now()
    date  = now.strftime('DATE,%Y/%m/%d\n')
    time  = now.strftime('TIME,%H:%M:%S\n')
    fn    = os.path.splitext(os.path.basename(filename))[0]
    # File header

    output = io.StringIO()

    output.write("separated\n");
    output.write("FILE,{}.dpv\n".format(fn))
    output.write("PCBFILE,SPCoast CHMT Processor\n")
    output.write(date)
    output.write(time)
    output.write("PANELYPE,0\n")             # Typo is correct. Type 0 = batch of PCBs. Type 1 = panel of PCBs.
    output.write("\n")                       # See addBatch() for details
    output.write("\n")
    contents = output.getvalue()
    output.close()
    return contents

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
            stack=stacknumber, fnum=int(f[CHMTPickNPlace.feedernum]), fXoff=float(f[CHMTPickNPlace.feederXoff]), fYoff=float(f[
                                                                                                                           CHMTPickNPlace.feederYoff]),
            pullDist=int(f[CHMTPickNPlace.pulldist]), name=f[CHMTPickNPlace.partname], placeHeight=float(f[
                                                                                                       CHMTPickNPlace.placeheight]), placeSpeed=int(f[
                                                                                                                                                     CHMTPickNPlace.placespeed]),
            options=f[CHMTPickNPlace.options],
            sizeX=float(f[CHMTPickNPlace.partsizeX]), sizeY=float(f[CHMTPickNPlace.partsizeY]),
            pickHeight=float(f[CHMTPickNPlace.pickheight]), pickDelay=float(f[CHMTPickNPlace.pickdelay]), pullSpeed=int(f[
                                                                                                                      CHMTPickNPlace.pullspeed])))
        stacknumber = stacknumber + 1
    output.write("\n")
    contents = output.getvalue()
    output.close()
    return contents


def outputBatch():
    output = io.StringIO()
    #    Batch takes multiple copies of the same board and mounts them into the machine at the same time.
    #    This is different from an array where you have one PCB with X number of design copies in a panel
    #    Reference from outputHeader():
    #        If you are doing a batch then the header is
    #        PANELYPE,0
    #        If you are doing an array then the header is
    #        PANELYPE,1
    #        The typo (missing "T") is correct.
    #
    #    When there is a batch of boards it looks like this
    output.write("Table,No.,ID,DeltX,DeltY\n");
    output.write("Panel_Coord,0,1,0,0\n");

    #    When you define an array you get this:
    #     IntervalX = x spacing. Not sure if this is distance between array
    #     NumX = number of copies in X direction
    #print("Table,No.,ID,IntervalX,IntervalY,NumX,NumY")
    #print("Panel_Array,0,1,0,0,2,2")

    #    If you have an X'd out PCB in the array you can add a skip record.
    #    When you add a skip, you get another
    #print("Panel_Array,1,4,0,0,2,2")    # Skip board #4 in the array
    #    This doesn't quite make sense but skips will most likely NOT be automated
    contents = output.getvalue()
    output.close()
    return contents


def outputParts(parts, feeder):
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

        output.write( "EComponent, "
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


#    Add any IC tray info
def outputICTray():
    output = io.StringIO()
    output.write("Table,No.,ID,CenterX,CenterY,IntervalX,IntervalY,NumX,NumY,Start\n")
    contents = output.getvalue()
    output.close()
    return contents


def outputPCBCalibrate():
    output = io.StringIO()
    #   Flags to say what type and if calibration of the board has been done
    output.write("\n")
    output.write("Table,No.,nType,nAlg,nFinished\n")
    output.write("PcbCalib,0,1,0,0\n")

    #    Type: 0 = use components as calibration marks, 1 = use marks as calibration marks
    #    Finished: ? 0 = you haven't cal'd a board, 1 = you have cal'd the board
    contents = output.getvalue()
    output.close()
    return contents


def outputFiducials():
    output = io.StringIO()
    #   Adds the fiducials or mark information about this board or panel
    #   TODO - Should we pull in the marks from the PCB file? It might make better
    #   sense to have user do this manually as it will be pretty specific.
    output.write("\n")
    output.write("Table,No.,ID,offsetX,offsetY,Note\n")
    output.write("CalibPoint,0,1,0.750,0.350,Mark1\n")
    output.write("CalibPoint,1,2,1.525,0.725,Mark3\n")
    contents = output.getvalue()
    output.close()
    return contents


def outputCalibrationFactor():
    output = io.StringIO()
    #   Add the calibration factor. This is all the offsets calculated when the
    #   PCB is calibrated. We don't have to set anything here because the program
    #   will calculate things after user calibrates the PCB.

    output.write("\n")
    output.write("Table,No.,DeltX,DeltY,AlphaX,AlphaY,BetaX,BetaY,DeltaAngle\n")
    output.write("CalibFator,0,0,0,0,0,1,1,0\n") # Typo is required
    contents = output.getvalue()
    output.close()
    return contents


"""
main() 

usage: eagle2chmt.py [-h] pcbfile [pcbfile ...]

Create a CHMT pick-n-place job from an EAGLEcad PCB board file.

positional arguments:
  pcbfile     an EAGLEcad .brd file to process

optional arguments:
  -h, --help  show this help message and exit


"""

def main():
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
    
    parser = argparse.ArgumentParser(description='Create a CHMT pick-n-place job from an EAGLEcad PCB board file.',
				     formatter_class=argparse.RawDescriptionHelpFormatter,
				     epilog="""
    Feederfile has the structure:
       Tape Size,Feeder Number,Component,Feeder XOffset,Feeder YOffset,...
       ...PickHeight,PickDelay,PullSpeed,Pull Distance,Place Height,Place Speed,...
       ...Head,Part Rotation,Place Component,Check Vacuum,Use Vision,...
       ...Size X,Size Y,Centroid Correction X,Centroid Correction Y,Aliases,...
       ...Stock Notes,Inventory Notes,Used On


       Tape Size is 8mm, 12mm...
       Component is the name of the component as (value-package)
       Pull Distance is the tape spacing between components: 2-4-8-12-16-24
       Part Rotation is the difference between the eagle library footprint and the orientation on the tape
       Place Component is Y or N if you want to skip placing this component
       Aliases is a ':' delimited list of altername component ids
       Stock Notes,Inventory Notes,Used On are all ignored comment fields

    """)
    parser.add_argument('PCBfile', metavar='pcbfile', type=str, nargs='+',
			help='an EAGLEcad .brd file to process')
    parser.add_argument("--eagleRC",    help="Eagle rc file with palette definitions")
    parser.add_argument("--feederfile", help="csv file with feeder component assignments")
    parser.add_argument("--outdir",     help="output directory (default is <PCBfile>.bom.txt)")
    parser.add_argument("--download",   action="store_true", help="download a fresh feeder file from Google Sheets?")
    parser.add_argument("--key",        help="Google Sheets document access key")

    args = parser.parse_args()
    args.config = configuration
    
    feederfile = args.config.get('EagleTools', 'defaultfeederfile')
    if args.feederfile:
	    feederfile = args.feederfile

    rcfile = args.config.get('EagleTools', 'defaulteaglerc')
    if args.eagleRC:
	    rcfile = args.eagleRC

    if (args.download or not os.path.isfile(feederfile) ):
	    print("DL feederfile: ", feederfile)
	    CHMTPickNPlace.downloadFeederFile(args, feederfile, args.key)

    (feeder, component) = CHMTPickNPlace.loadFeeders(feederfile)
    palettes = EagleCAD.getLayers(rcfile)

    for f in args.PCBfile:
    	if len(args.PCBfile) > 1:
    	    print("Processing {}".format(f))

    	outfilename = os.path.splitext(os.path.basename(f))[0] + ".dpv"
    	outdir = os.path.dirname(f)

        if args.outdir:
            if args.outdir == '@':
                outdir = args.config.get('EagleTools', 'defaultBOMdir')
            elif args.outdir == "-":
                pass
            else:
                outdir = args.outdir
                
        bn = os.path.basename(outfilename)
        outfilename = os.path.join(outdir, bn)

    	(eagleBoard, packages, layers) = EagleCAD.loadBoard(f, palettes)
    	parts    = EagleCAD.getSMDParts(eagleBoard, packages, component, feeder)
    	used     = EagleCAD.getUsedComponents(parts, feeder)

    	content = ""
    	content = content + outputHeader(f)
    	content = content + outputStations(used, feeder, component)
    	content = content + outputBatch()
    	content = content + outputParts(parts, feeder)
    	content = content + outputICTray()
    	content = content + outputPCBCalibrate()
    	content = content + outputFiducials()
    	content = content + outputCalibrationFactor()

    	outfile = open(outfilename, "w")
    	outfile.write(content)
    	outfile.close()


if __name__ == "__main__":
    main()

