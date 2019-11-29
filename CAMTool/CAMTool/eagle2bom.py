#!/usr/bin/env python3

"""
Author: John Plocher, 2019
URL:    www.SPCoast.com
License: Python Software Foundation License

Generate a parts BOM used in an Eagle project

  -John Plocher
   July 2018
   www.SPCoast.com

"""
import configparser
from pkg_resources import Requirement, resource_filename
import CAMTool.fab.SiteConfiguration as config
from CAMTool.fab import CHMTPickNPlace, EagleCAD

import sys
import argparse
import io
import os.path
import re


def sorted_nicely(l):
    """ Sorts the given iterable in the way that is expected.

    Required arguments:
    l -- The iterable to be sorted.

    """
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanum_key)


def try_int(s):
    "Convert to integer if possible."
    try:
        return int(s)
    except:
        return s


def natsort_key(s):
    "Used internally to get a tuple by which s is sorted."
    import re
    return list(map(try_int, re.findall(r'(\d+|\D+)', s)))


def natcmp(a, b):
    "Natural string comparison, case sensitive."
    return cmp(natsort_key(a), natsort_key(b))


def outputParts(parts, smt, pth):
    return outputPartsMD(parts, smt, pth)

def outputPartsMD(parts, smt, pth):
    output = io.StringIO()
    partcounts = {}

    # by part name, with common values collected together...
    for pn in sorted(iter(parts.keys()), key=EagleCAD.natural_sort_key):
        p = parts[pn]
        # p['id'] == part value - package
        if p['id'] in partcounts:
            partcounts[p['id']]['cnt'] += 1
            partcounts[p['id']]['list'].append(p)

        else:
            partcounts[p['id']] = {}
            partcounts[p['id']]['cnt'] = 1
            partcounts[p['id']]['list'] = []
            partcounts[p['id']]['p'] = p
            partcounts[p['id']]['list'].append(p)

            if 'feeder' in p:
                partcounts[p['id']]['feed'] = p['feeder']


    output.write("{:.partlist}\n")  # CSS styling class...
    output.write("| Parts | Value | Package | Quantity | Library | Type/Feeder\n")

    for pn in sorted(iter(partcounts.keys()), key=EagleCAD.natural_sort_key):

        count = partcounts[pn]['cnt']
        list  = partcounts[pn]['list']
        f     = partcounts[pn]['feed']
        p     = partcounts[pn]['p']

        if      not pn.startswith("#-") \
            and not pn.startswith("target-") \
            and not pn.startswith("no_load-") \
            and not pn.startswith("mount-") \
            and not pn.startswith("fidicual-") \
            and list :

            if f == CHMTPickNPlace.SKIP:
                if pth:
                    output.write('|-\n')
                    sep='| '
                    for p in sorted(list, cmp=natcmp, key=lambda i: i['name']):
                        output.write('{}{}'.format(sep, p['name']))
                        sep = ', '
                    output.write(" | {} | {} | {}x | {} | {}\n".format(p['value'], p['package'], count, p['library'], 'PTH'))
            elif f == CHMTPickNPlace.NOTFOUND:
                if smt:
                    output.write('|-\n')
                    sep='| '
                    for p in sorted(list, cmp=natcmp, key=lambda i: i['name']):
                        output.write('{}{}'.format(sep, p['name']))
                        sep = ', '
                    output.write(" | {} | {} | {}x | {} | {}\n".format(p['value'], p['package'], count, p['library'], 'NONE'))
            else:
                if smt:
                    output.write('|-\n')
                    sep='| '
                    for p in sorted(list, cmp=natcmp, key=lambda i: i['name']):
                        output.write('{}{}'.format(sep, p['name']))
                        sep = ', '
                    output.write(" | {} | {} | {}x | {} | {}\n".format(p['value'], p['package'], count, p['library'], f))

    contents = output.getvalue()
    output.close()
    return contents

def outputPartsWiki(parts, smt, pth):
    output = io.StringIO()
    partcounts = {}

    # by part name, with common values collected together...
    for pn in parts.keys():
        p = parts[pn]
        # p['id'] == part value - package
        if p['id'] in partcounts:
            partcounts[p['id']]['cnt'] += 1
            partcounts[p['id']]['list'].append(p)

        else:
            partcounts[p['id']] = {}
            partcounts[p['id']]['cnt'] = 1
            partcounts[p['id']]['list'] = []
            partcounts[p['id']]['p'] = p
            partcounts[p['id']]['list'].append(p)

            if 'feeder' in p:
                partcounts[p['id']]['feed'] = p['feeder']


    output.write("""
==Parts List==
<blockquote>
{| class="wikitable"
! Parts
! Value
! Package
! Quantity
! Feeder
""")
    for pn in sorted(iter(partcounts.keys()), key=EagleCAD.natural_sort_key):
        count = partcounts[pn]['cnt']
        list  = partcounts[pn]['list']
        f     = partcounts[pn]['feed']
        p     = partcounts[pn]['p']

        if      not pn.startswith("-") \
            and not pn.startswith("target-") \
            and not pn.startswith("no_load-") \
            and not pn.startswith("mount-") \
            and not pn.startswith("fidicual-") \
            and list :

            if f == CHMTPickNPlace.SKIP:
                if pth:
                    output.write('|-\n')
                    sep='| '
                    for p in sorted(list, cmp=natcmp, key=lambda i: i['name']):
                        output.write('{}{}'.format(sep, p['name']))
                        sep = ', '
                    output.write("\n| {} \n| {} \n| {}x \n| {}\n".format(p['value'], p['package'], count, 'PTH'))
            elif f == CHMTPickNPlace.NOTFOUND:
                if smt:
                    output.write('|-\n')
                    sep='| '
                    for p in sorted(list, cmp=natcmp, key=lambda i: i['name']):
                        output.write('{}{}'.format(sep, p['name']))
                        sep = ', '
                    output.write("\n| {} \n| {} \n| {}x \n| {}\n".format(p['value'], p['package'], count, 'NONE'))
            else:
                if smt:
                    output.write('|-\n')
                    sep='| '
                    for p in sorted(list, cmp=natcmp, key=lambda i: i['name']):
                        output.write('{}{}'.format(sep, p['name']))
                        sep = ', '
                    output.write("\n| {} \n| {} \n| {}x \n| {}\n".format(p['value'], p['package'], count, f))

    output.write("|}\n</blockquote>\n")

    contents = output.getvalue()
    output.close()
    return contents

def main():
    """
    main() 

    usage: eagle2bom.py [-h] [--eagleRC EAGLERC] [--feederfile FEEDERFILE]
            [--outdir OUTDIR] [--download] [--smt] [--pth] [--key KEY]
            pcbfile [pcbfile ...]

    Create a parts list BOM from an EAGLEcad PCB board file(s).
    The BOM file will be named <pcbfile_basename>.bom.md and
    will be in markdown table format

    positional arguments:
      pcbfile               an EAGLEcad .brd file to process

    optional arguments:
      -h, --help            show this help message and exit
      --eagleRC EAGLERC     Eagle rc file with palette definitions
      --feederfile FEEDERFILE
                csv file with feeder component assignments
      --outdir OUTDIR       output directory (default is <PCBfile>.bom.txt)
      --download            download a fresh feeder file from Google Sheets?
      --smt                 SMT parts only?
      --pth                 PTH parts only?
      --key KEY             Google Sheets document access key

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
    
    parser = argparse.ArgumentParser(description='Create a parts list BOM from an EAGLEcad PCB board file(s).\n'
                         'The BOM file will be named <pcbfile_basename>.bom.wiki and\n'
                         'will be in MediaWiki table format',
                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('PCBfile', metavar='pcbfile', type=str, nargs='+',
            help='an EAGLEcad .brd file to process')
    parser.add_argument("--eagleRC",    help="Eagle rc file with palette definitions")
    parser.add_argument("--feederfile", help="csv file with feeder component assignments")
    parser.add_argument("--outdir",     help="output directory (default is <PCBfile>.bom.txt)")
    parser.add_argument("--download",   action="store_true", help="download a fresh feeder file from Google Sheets?")
    parser.add_argument("--smt",        action="store_true", help="SMT parts only?")
    parser.add_argument("--pth",        action="store_true", help="PTH parts only?")
    parser.add_argument("--key",        help="Google Sheets document access key")
    parser.add_argument('--verbose',   '-v',  action='store_true', help='Verbose flag')
    

    args = parser.parse_args()
    args.config = configuration
    feederfile = args.config.get('EagleTools', 'defaultfeederfile')
    if args.feederfile:
        feederfile = args.feederfile

    rcfile = args.config.get('EagleTools', 'defaulteaglerc')
    if args.eagleRC:
        rcfile = args.eagleRC

    if not args.smt and not args.pth:
        args.smt = args.pth = True

    if (args.download or not os.path.isfile(feederfile) ):
        print("Downloading feederfile: ", feederfile)
        CHMTPickNPlace.downloadFeederFile(args, feederfile, args.key)

    (feeder, component) = CHMTPickNPlace.loadFeeders(feederfile)
    palettes = EagleCAD.getLayers(rcfile)

    for f in args.PCBfile:
        if args.verbose or len(args.PCBfile) > 1:
            print("Processing {}".format(f))

        outfilename = os.path.splitext(os.path.basename(f))[0] + ".bom.md"
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

        content = outputParts(parts, args.smt, args.pth)
        if args.outdir == '-':
            print(content)
        else:
            with open(outfilename, "w") as outfile:
                outfile.write(outputParts(parts, args.smt, args.pth))



if __name__ == "__main__":
    main()

