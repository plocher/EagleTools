#!/usr/bin/python
"""
Author: John Plocher, 2019
URL:    www.SPCoast.com
License: Python Software Foundation License

Generate a TOC for an EAGLE CAD library
"""

from CAMTool.fab.SiteConfiguration import *

import argparse
import StringIO
from fab import EagleCAD
import os.path


def try_int(s):
    "Convert to integer if possible."
    try:
        return int(s)
    except:
        return s


def natsort_key(s):
    "Used internally to get a tuple by which s is sorted."
    import re
    return map(try_int, re.findall(r'(\d+|\D+)', s))


def natcmp(a, b):
    "Natural string comparison, case sensitive."
    return cmp(natsort_key(a), natsort_key(b))


def outputTOC(args, eagleLibrary, packages, symbols):
    output = StringIO.StringIO()

    output.write("""
==Library TOC List==
<blockquote>
""")
    output.write("</blockquote>\n")

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
    The BOM file will be named <pcbfile_basename>.bom.wiki and
    will be in MediaWiki table format

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


    parser = argparse.ArgumentParser(description='Create a Package list TOC from an EAGLEcad Library(s).\n'
						 'The TOC file will be named <pcbfile_basename>.toc.wiki and\n'
						 'will be in MediaWiki table format',
				     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('Library', metavar='libfile', type=str, nargs='+',
			help='an EAGLEcad .lib file to process')
    parser.add_argument("--eagleRC",    help="Eagle rc file with palette definitions")
    parser.add_argument("--outdir",     help="output directory (default is <PCBfile>.bom.txt)")
    parser.add_argument("--smt",        action="store_true", help="SMT parts only?")
    parser.add_argument("--pth",        action="store_true", help="PTH parts only?")
    parser.add_argument("--key",        help="Google Sheets document access key")

    args = parser.parse_args()

    rcfile = defaulteaglerc
    if args.eagleRC:
	rcfile = args.eagleRC

    if not args.smt and not args.pth:
	args.smt = args.pth = True

    palettes = EagleCAD.getLayers(rcfile)

    for f in args.Library:
	if len(args.Library) > 1:
	    print "Processing {}".format(f)

	outfilename = os.path.splitext(os.path.basename(f))[0] + ".bom.wiki"
	outdir = os.path.dirname(f)

	if args.outdir:
	    if args.outdir == '@':
		outdir = defaultBOMdir
	    elif args.outdir == "-":
		pass
	    else:
		outdir = args.outdir
	    bn = os.path.basename(outfilename)

	    outfilename = os.path.join(outdir, bn)

	(eagleLibrary, packages, symbols) = EagleCAD.loadLibrary(f)


	content = outputTOC(args, eagleLibrary, packages, symbols)
	if args.outdir == '-':
	    print content
	else:
	    with open(outfilename, "w") as outfile:
		outfile.write(content)


if __name__ == "__main__":
    main()

