#!/usr/bin/env python3

"""
Author: John Plocher, 2019
URL:    www.SPCoast.com
License: Python Software Foundation License

eagle2gerbers

    Create an Eagle Schematic and Board (.sch and .brd files) for a design, then
    Run this tool to generate Gerber files, images and part placement files for your design.

    This job will generate the following files:

    * excellon drill data, top and bottom copper, silk and soldermask, top solderpaste and
      a board outline in Gerber 274x format files.  These files will have names ending in
          "TXT" "GTL" "GTS" "GTP" "GBP" "GTO" "GBL" "GBS" "GBO" and "GML".

    * Board images in .svg and .png forms, of the board's front and back, with and without
      silkscreen.

    * Fabreication support files

    Once the files have been generated, run this script in the Eagle project directory to
    collect all the gerber files generated by the CAM processor together into a compressed tar
    or zip file for submission to a board fab house such as BatchPCB or Seeed Studios.

    The script archives the files along with a copy of the schematic and board files so
    that you can go back and reproduce historical versions if needed.

    Finally, it copies the gerber files (.tar or .zip) into an "order collection" directory,
    usually in your home directory, so you can easily find all the boards that need to be ordered
    next time you place a fab order.
"""

import configparser
from pkg_resources import Requirement, resource_filename
import CAMTool.fab.SiteConfiguration as config

import sys
import os
import os.path
import argparse
import datetime
from zipfile import ZipFile
import tarfile
import shutil


"""
Ensure file naming patterns are consistent by generating them in one place

#  gerber files contain data for:
#
#  Gerber Top Layer (copper layer):             *.GTL
#  Gerber Top Overlay (silkscreen layer):       *.GTO
#  Gerber Top Soldermask (soldermask layer):    *.GTS
#  Gerber Bottom Layer (copper layer):          *.GBL
#  Gerber Bottom Overlay (silkscreen layer):    *.GBO
#  Gerber Bottom Soldermask (soldermask layer): *.GBS
#  Gerber Milling Layer:                        *.GML
#  Gerber Board Outline:                        *.GKO
#  Gerber Top solderPaste (smt solder layer):   *.GTP
# and
#  Excellon Drill File:                         *.TXT

"""

def boardfilename(project):
    return "{}.brd"        .format(project)

def schematicfilename(project):
    return "{}.sch"        .format(project)

def genGerberFilenameList(project):
    FileList = {}
    FileList['GTL'] = "{}.GTL".format(project)
    FileList['GTS'] = "{}.GTS".format(project)
    FileList['GTP'] = "{}.GTP".format(project)
    FileList['GTO'] = "{}.GTO".format(project)

    FileList['GML'] = "{}.GML".format(project)
    FileList['GKO'] = "{}.GKO".format(project)

    FileList['GBO'] = "{}.GBO".format(project)
    FileList['GBP'] = "{}.GBP".format(project)
    FileList['GBS'] = "{}.GBS".format(project)
    FileList['GBL'] = "{}.GBL".format(project)

    FileList['TXT'] = "{}.TXT".format(project)
    return FileList

def genEagleFilenameList(project):
    FileList = {}
    FileList['board']       = boardfilename(project)   # + .brd
    FileList['boardArray']  = boardfilename("{}_array"  .format(project))   # + .brd
    FileList['boardScript'] = boardfilename("{}_array.scr"  .format(project))
    FileList['schematic']   = schematicfilename(project)   # + .sch
    return FileList

def genArchivesFileList(project):
    FileList = {}
    FileList['tefn']       = '{}.eagle.tar'  .format(project)       # Tar Eagle File Name
    FileList['zefn']       = '{}.eagle.zip'  .format(project)
    FileList['tgfna']      = '{}_array.gerbers.tar'.format(project) # Tar Gerbers File Name - Array
    FileList['zgfna']      = '{}_array.gerbers.zip'.format(project)
    FileList['tgfn']       = '{}.gerbers.tar'.format(project)
    FileList['zgfn']       = '{}.gerbers.zip'.format(project)       # Zip Gerber File Name
    return FileList


def genPickNPlaceList(project):
    FileList = {}
    # pick-n-place control file (*.DPV)
    FileList['dpv']        = "{}.dpv"        .format(project)

    return FileList


def genDerivedFileList(project):
    FileList = {}

    # Info file / Bill Of Materials
    FileList['bom']        = "{}.bom.md"     .format(project)
    FileList['csv']        = "{}.parts.csv"  .format(project) # from generate_csv_partlist.ulp
    # Board Image (experimental)
    FileList['svg']        = "{}.svg"        .format(project)

    FileList['pngsch']     = "{}.sch.png"    .format(project)
    FileList['pngbrd']     = "{}.brd.png"    .format(project)
    FileList['pngbot']     = "{}.bot.brd.png".format(project)
    FileList['pngtop']     = "{}.top.brd.png".format(project)

    return FileList


def genTempFileList(project):
    FileList = {}
    for f in ["GBP", "job", "dri", "gpi", "pro",
              "b##", "b#1", "b#2", "b#3", "b#4", "b#5", "b#6", "b#7", "b#8", "b#9",
              "s##", "s#1", "s#2", "s#3", "s#4", "s#5", "s#6", "s#7", "s#8", "s#9"]:
        fn = "{NAME}.{EXT}".format(NAME=project, EXT=f)
        FileList[f] = fn


def genBoardFilenameList(args, project):
    FileList = {}
    for n, f in genEagleFilenameList(project).items():
        FileList[n] = f
    for n, f in genDerivedFileList(project).items():
        FileList[n] = f
    for n, f in genArchivesFileList(project).items():
        FileList[n] = f
    if args.picknplace:
        for n, f in genPickNPlaceList(project).items():
            FileList[n] = f
    return FileList

def getCADtime(schematic, board):
    base_time = None
    if board is not None and os.path.isfile(board):
        base_time = os.stat(board).st_mtime  # time of most recent content modification

    if schematic is not None and os.path.isfile(schematic):
        s_modified_time = os.stat(schematic).st_mtime
        if base_time is None or s_modified_time > base_time:
            base_time = s_modified_time

    return base_time

"""
Generate a zip or tar file of the gerbers
"""
def generateGerbersFromEagle(args):
    def callCommand(args, file, board, command, layers):
        command = "{COMMAND} -o{out} {board} {layers}" .format(COMMAND=command,
                                                                out=file,
                                                                board=board,
                                                                layers=layers)
        if args.verbose:
            print('% {}'.format(command))
        os.system(command)

    GENGERBER   = args.config.get('EagleTools', 'GENGERBER')
    GENDRILLS   = args.config.get('EagleTools', 'GENDRILLS')
    ARCHIVEDIR  = args.config.get('EagleTools', 'ARCHIVEDIR')
    ALINK       = args.config.get('EagleTools', 'ALINK')

    singletonbase = args.project
    panelbase     = "{}_array".format(args.project)

    singleton = boardfilename(singletonbase)
    panel     = boardfilename(panelbase)
    schematic = schematicfilename(singletonbase)

    if not os.path.isfile(singleton):
        if not os.path.isfile(panel):
            s='# ERROR: Can not create gerbers without a brd file ({} or {})...'
            raise Exception(s.format(singleton, panel))

    modified  = False
    for project in [singletonbase, panelbase]:

        blist = genBoardFilenameList(args, project)
        b     = boardfilename(project)

        if not os.path.isfile(b):
            continue

        FileList = genGerberFilenameList(project)

        needed = False

        if args.force:
            needed = True
            if args.verbose:
                print("** FORCE regeneration of gerbers for {}\n".format(args.project))

        if not needed:
            base_time = getCADtime(schematic, b)

            """
            base_time is the CAD file set's last mod time.
            
            If Archive/Current/... is older than .sch/.brd, or not there, needed!
     
            """
            foundarchive = False
            if not args.noarchive:
                for d in [ '.', os.path.join(ARCHIVEDIR, ALINK) ]:
                    for a in [ blist['tgfn'], blist['zgfn'] ]:
                        fullname = os.path.join(d, a)
                        if os.path.isfile(fullname):
                            foundarchive = True
                            tar_modified_time = os.stat(fullname).st_mtime
                            if base_time > tar_modified_time:
                                if args.verbose:
                                    print("** Archive Dir content is older than current CAD files\n")
                                needed = True

            if not foundarchive:
                if args.verbose:
                    if not args.noarchive:
                        print("** Archive not found\n")
                needed = True

        if not needed:
            continue

        modified = True

        # clean out old gerber files so EagleCad doesn't ask to overwrite them
        for n,f in FileList.items():
            if os.path.isfile(f):
                os.remove(f)

        # explicitly run EagleCAD CAM jobs to create the needed PCB Fab files
        #
        # These files, zipped together, are the only files you need to have a PCB made at nearly any fab house.

        # Copper layers
        callCommand(args, FileList['GTL'], b, GENGERBER, args.config.get('EagleTools', 'L_GTL'))
        callCommand(args, FileList['GBL'], b, GENGERBER, args.config.get('EagleTools', 'L_GBL'))

        # Solder Mask
        callCommand(args, FileList['GTS'], b, GENGERBER, args.config.get('EagleTools', 'L_GTS'))
        callCommand(args, FileList['GBS'], b, GENGERBER, args.config.get('EagleTools', 'L_GBS'))

        # Solder Paste
        callCommand(args, FileList['GTP'], b, GENGERBER, args.config.get('EagleTools', 'L_GTP'))
        callCommand(args, FileList['GBP'], b, GENGERBER, args.config.get('EagleTools', 'L_GBP'))

        # Board Outline and Milling instructions
        callCommand(args, FileList['GML'], b, GENGERBER, args.config.get('EagleTools', 'L_GML'))
        # Board Outline only
        callCommand(args, FileList['GKO'], b, GENGERBER, args.config.get('EagleTools', 'L_GKO'))

        # Drills and holes
        callCommand(args, FileList['TXT'], b, GENDRILLS, args.config.get('EagleTools', 'L_TXT'))

        # Silk Screen layers
        if b == singleton:
            callCommand(args, FileList['GTO'], b, GENGERBER, args.config.get('EagleTools', 'L_GTO'))
            callCommand(args, FileList['GBO'], b, GENGERBER, args.config.get('EagleTools', 'L_GBO'))
        else:  # panel
            callCommand(args, FileList['GTO'], b, GENGERBER, args.config.get('EagleTools', 'LA_GTO'))
            callCommand(args, FileList['GBO'], b, GENGERBER, args.config.get('EagleTools', 'LA_GBO'))

        # Gerbers for fabrication
        if args.tar:
            if args.verbose:
                print('Archive Gerbers: Tar: {}'.format(blist['tgfn']))
            with tarfile.open(blist['tgfn'], 'w') as tar:
                for n, f in FileList.items():
                    if os.path.isfile(f):
                        if args.verbose:
                            print('\t{}'.format(f))
                        tar.add(f)
        else:
            if args.verbose:
                print('Archive Gerbers: Zip: {}'.format(blist['zgfn']))
            with ZipFile(blist['zgfn'], 'w') as zip:
                for n, f in FileList.items():
                    if os.path.isfile(f):
                        if args.verbose:
                            print('\t{}'.format(f))
                        zip.write(f)

    # now, make archives of the CAM files and the gerbers we just generated
    # Sources:  archive the sch, brd, _array.brd and _array_scr files together
    if args.tar:
        if b == singleton:
            if args.verbose:
                print('Archive CAD sources: Tar: {}'.format(blist['tefn']))
            with tarfile.open(blist['tefn'], 'w') as tar:
                for f in [schematic, singleton, panel, blist['boardScript']]:
                    if os.path.isfile(f):
                        if args.verbose:
                            print('\tAdd {}'.format(f))
                        tar.add(f)
    else:
        if b == singleton:
            # only create a single archive of sch
            if args.verbose:
                print('Archive CAD sources: Zip: {}'.format(blist["zefn"]))
            with ZipFile(blist["zefn"], 'w') as zip:
                for f in [schematic, singleton, panel, blist['boardScript']]:
                    if os.path.isfile(f):
                        if args.verbose:
                            print('\tAdd {}'.format(f))
                        zip.write(f)
    return modified


def generateImagesFromEagle(args):

    # EagleCAD commands
    PARTS_BOARD=args.config.get('EagleTools', 'PARTS_BOARD')
    if PARTS_BOARD is None or PARTS_BOARD == '':
        PARTS_BOARD = 'OPTIMIZE'

    IMAGE_BOARD=args.config.get('EagleTools', 'IMAGE_BOARD')
    if IMAGE_BOARD is None or IMAGE_BOARD == '':
        IMAGE_BOARD = 'OPTIMIZE'

    IMAGE_SCH=args.config.get('EagleTools', 'IMAGE_SCH')
    if IMAGE_SCH is None or IMAGE_SCH == '':
        IMAGE_SCH = 'OPTIMIZE'

    IMAGE_BSILK=args.config.get('EagleTools', 'IMAGE_BSILK')
    if IMAGE_BSILK is None or IMAGE_BSILK == '':
        IMAGE_BSILK = 'OPTIMIZE'

    IMAGE_TSILK=args.config.get('EagleTools', 'IMAGE_TSILK')
    if IMAGE_TSILK is None or IMAGE_TSILK == '':
        IMAGE_TSILK = 'OPTIMIZE'

    singletonbase = args.project
    panelbase = "{}_array".format(args.project)

    schematic = schematicfilename(singletonbase)
    needed = False
    modified = False

    if args.force:
        needed = True
        if args.verbose:
            print("** FORCE {}\n".format(args.project))

    # generate image of schematic ...
    if os.path.isfile(schematic):
        base_time = None

        blist = genBoardFilenameList(args, singletonbase)

        dependent_list = [blist['pngsch']]
        for dependent in dependent_list:
            if os.path.isfile(dependent):
                d_time = os.stat(dependent).st_mtime
                if base_time > d_time:
                    base_time = d_time
            else:
                needed = True

        if needed or base_time is None or base_time < os.stat(schematic).st_mtime:
            modified = True
            for dependent in dependent_list:
                if os.path.isfile(dependent):
                    os.remove(dependent)
            IMAGE_SCH = "script SPCoastlayers.scr; script defaultcolors.scr; SET PALETTE WHITE; DISPLAY {layer}; EXPORT image {png} 300".format(
                layer=args.config.get('EagleTools', 'D_SCHEMATIC'),
                png=blist['pngsch'])

            ECMD="SET CONFIRM OFF;{};undo;quit;".format(IMAGE_SCH)

            c="{EAGLE} -C \"{cmd}\" {file}".format(EAGLE=args.config.get('EagleTools', 'EAGLEAPP'), cmd=ECMD, file=schematic)
            if args.verbose:
                print("+ {}".format(c))
            os.system(c)

    needed = False
    if args.force:
        needed = True
    # ... and for the board (and _array.brd, if exists)
    for project in [singletonbase, panelbase]:
        base_time = None

        blist = genBoardFilenameList(args, project)
        b = boardfilename(project)

        if not os.path.isfile(b):
            continue

        dependent_list = [ blist['pngbrd'], blist['pngbot'], blist['pngtop'] ]

        for dependent in dependent_list:
            if os.path.isfile(dependent):
                d_time = os.stat(dependent).st_mtime
                if base_time > d_time:
                    base_time = d_time
            else:
                needed = True

        if needed or base_time is None or base_time < os.stat(schematic).st_mtime:
            modified = True
            for dependent in dependent_list:
                if os.path.isfile(dependent):
                    os.remove(dependent)

            IMAGE_BOARD = IMAGE_BOARD.format(
                                                layer=args.config.get('EagleTools', 'D_NORMAL'),
                                                png=blist['pngbrd'])
            IMAGE_BSILK = IMAGE_BSILK.format(
                                                layer=args.config.get('EagleTools', 'D_BSILK'),
                                                png=blist['pngbot'])
            IMAGE_TSILK = IMAGE_TSILK.format(
                                                layer=args.config.get('EagleTools', 'D_TSILK'),
                                                png=blist['pngtop'])

            ECMD="SET CONFIRM OFF;{};undo;{};undo;undo;{};undo;{};undo;quit;"
            ECMD=ECMD.format(PARTS_BOARD, IMAGE_BOARD, IMAGE_BSILK,IMAGE_TSILK)

            c = "{EAGLE} -C \"{cmd}\" {board}".format(
                                                EAGLE=args.config.get('EagleTools', 'EAGLEAPP'),
                                                cmd=ECMD,
                                                board=b)
            if args.verbose:
                print("+ {}".format(c))
            os.system(c)
    return modified


def generate_DESCRIPTION(args):
    if not os.path.isfile("DESCRIPTION"):
        f = open("DESCRIPTION", "w")
        f.write("{}\n\n".format(args.project))
        f.close()

def isNeeded(file, base_time):
    if os.path.isfile(file):
        modified_time = os.stat(file).st_mtime
        return base_time > modified_time
    return True


def generateFabFiles(args):
    def callCommand(args, command, board):
        command = "{COMMAND} --feederfile=/tmp/PnP-feeders {BOARD}".format(COMMAND=command, BOARD=board)
        if args.verbose:
            print('% {}'.format(command))
        os.system(command)

    singletonbase = args.project
    panelbase     = "{}_array".format(args.project)

    singleton = boardfilename(singletonbase)
    panel     = boardfilename(panelbase)
    schematic = schematicfilename(singletonbase)

    if not os.path.isfile(singleton):
        if not os.path.isfile(panel):
            s='# ERROR: Can not create fab files without a brd file ({} or {})...'
            raise Exception(s.format(singleton, panel))

    for project in [singletonbase, panelbase]:

        blist = genBoardFilenameList(args, project)
        b = boardfilename(project)

        if not os.path.isfile(b):
            continue

        base_time = getCADtime(schematic, b)

        if args.picknplace:
            if isNeeded(blist['dpv'], base_time):
                callCommand(args, args.config.get('EagleTools', 'eagle2chmt'), b)
        if isNeeded(blist['svg'], base_time):
            callCommand(args, args.config.get('EagleTools', 'eagle2svg'),  b)
        if isNeeded(blist['bom'], base_time):
            callCommand(args, args.config.get('EagleTools', 'eagle2bom'),  b)


def clean(args):
    singletonbase = args.project
    panelbase = "{}_array".format(args.project)

    for project in [singletonbase, panelbase]:
        if not args.leave:
            for d in [genGerberFilenameList(project), genTempFileList(project)]:
                for n, f in d.items():
                    if os.path.isfile(f):
                        if args.verbose:
                            print('% rm {}'.format(f))
                        os.remove(f)




def generateArchive(args):
    DATE       = datetime.datetime.today().strftime('%F-%T')
    GERBERDIR  = 'Gerbers.{}.{}'.format(args.project, DATE)
    ARCHIVEDIR  = args.config.get('EagleTools', 'ARCHIVEDIR')
    ALINK       = args.config.get('EagleTools', 'ALINK')
    
    l = os.path.join(ARCHIVEDIR, ALINK)
    d = os.path.join(ARCHIVEDIR, GERBERDIR)

    if not os.path.isdir(ARCHIVEDIR):
        if args.verbose:
            print('mkdir {}'.format(ARCHIVEDIR))
        os.mkdir(ARCHIVEDIR, 0o755)

    if os.path.islink(l):
        if args.verbose:
            print('% rm {}'.format(l))
        os.remove(l)

    if args.verbose:
        print('% mkdir {}'.format(d))
    os.mkdir(d, 0o755)

    if args.verbose:
        print('% ln -s {} {}'.format(GERBERDIR, l))
    os.symlink(GERBERDIR, l)

    singletonbase = args.project
    panelbase = "{}_array".format(args.project)

    singleton = boardfilename(singletonbase)
    panel = boardfilename(panelbase)

    if not os.path.isfile(singleton):
        if not os.path.isfile(panel):
            s='# ERROR: Can not create fab files without a brd file ({} or {})...'
            raise Exception(s.format(singleton, panel))

    for project in [singletonbase, panelbase]:
        for dict in [genEagleFilenameList(project),
                     genArchivesFileList(project),
                     genDerivedFileList(project)]:
            for n, f in dict.items():
                if os.path.isfile(f):
                    if args.verbose:
                        print('% cp {} {}'.format(f, d))
                    shutil.copy(f, d)
    if not args.leave:
        clean()

def copyFiles2Order(args):
    d = args.config.get('EagleTools', 'DefaultOrdersDirectory')
    d = os.path.expanduser(d)
    if args.directory:
        ad = os.path.expanduser(args.directory)
        if os.path.exists(ad):
            d = ad

    if not os.path.exists(d):
        print("** Orders directory '{}' does not exist! ".format(d),)
        dparent = os.path.dirname(d)
        if os.path.exists(dparent):
            print("Creating it...")
            os.mkdir(d)
        else:
            print("Error: Can't create it, not copying files.")
            return

    singletonbase = args.project
    panelbase     = "{}_array".format(args.project)

    desired_files=[]
    for project in [singletonbase, panelbase]:

        blist = genBoardFilenameList(args, project)
        b     = boardfilename(project)

        if not os.path.isfile(b):
            continue

        if os.path.isfile(blist['tgfn']):
            desired_files.append(blist['tgfn'])
        if os.path.isfile(blist['zgfn']):
            desired_files.append(blist['zgfn'])

    if len(desired_files) > 0:
        s = args.stamp
        if s is None:
            s=''
        else:
            s = '-{}'.format(s)

        for f in desired_files:
            (name, ext) = os.path.splitext(f)
            (name, gerbers) = os.path.splitext(name)
            ext = '{}{}'.format(gerbers, ext)

            dest = "{}{}-10x10-GREEN{}".format(name, s, ext)
            dest = os.path.join(d, dest)
            if os.path.isfile(f):
                if args.verbose:
                    print('% cp {} {}'.format(f, dest))
                shutil.copy(f, dest)

def testconfig(args):
    # EagleCAD commands
    PARTS_BOARD = args.config.get('EagleTools', 'PARTS_BOARD')
    if PARTS_BOARD is None or PARTS_BOARD == '':
        PARTS_BOARD = 'OPTIMIZE'

    IMAGE_BOARD = args.config.get('EagleTools', 'IMAGE_BOARD')
    if IMAGE_BOARD is None or IMAGE_BOARD == '':
        IMAGE_BOARD = 'OPTIMIZE'

    IMAGE_SCH = args.config.get('EagleTools', 'IMAGE_SCH')
    if IMAGE_SCH is None or IMAGE_SCH == '':
        IMAGE_SCH = 'OPTIMIZE'

    IMAGE_BSILK = args.config.get('EagleTools', 'IMAGE_BSILK')
    if IMAGE_BSILK is None or IMAGE_BSILK == '':
        IMAGE_BSILK = 'OPTIMIZE'

    IMAGE_TSILK = args.config.get('EagleTools', 'IMAGE_TSILK')
    if IMAGE_TSILK is None or IMAGE_TSILK == '':
        IMAGE_TSILK = 'OPTIMIZE'

    print("PARTS_BOARD: {s}".format(s=PARTS_BOARD))
    print("IMAGE_BOARD: {s}".format(s=IMAGE_BOARD))
    print("IMAGE_SCH: {s}".format(s=IMAGE_SCH))
    print("IMAGE_BSILK: {s}".format(s=IMAGE_BSILK))
    print("IMAGE_TSILK: {s}".format(s=IMAGE_TSILK))


def main():
    """
    main()

    usage: eagle2CAM.py [-h] [--noarchive] [--picknplace] [--order]
                        [--directory DIRECTORY] [--tar] [--leave] [--verbose]
                        [--force] [--project PROJECT]

    optional arguments:
      -h, --help            show this help message and exit
      --noarchive, -n       Do not archive CAD files (default is to archive)
      --picknplace, -p      Generate Pick and Place .dpv files for CharmHigh
      --order, -o           copy gerber archive to orders directory
      --directory DIRECTORY, -D DIRECTORY
                            orders directory (default is
                            /Users/plocher/Dropbox/eagle/Seeed-
                            Orders/CurrentOrder)
      --tar, -t             create tar file for gerbers (default is zip)
      --leave, -l           Do not clean up unneeded files (default is to clean)
      --stamp VER, -s VER   Verbose flag
      --verbose, -v         Verbose flag
      --force, -f           Force rebuild flag
      --project PROJECT, -P PROJECT
                            Project name

    """

    somethingChanged = False

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
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--noarchive', '-n',  action='store_true', help='Do not archive CAD files (default is to archive)')
    parser.add_argument('--picknplace','-p',  action='store_true', help='Generate Pick and Place .dpv files for CharmHigh')
    parser.add_argument('--order',     '-o',  action='store_true', help='copy gerber archive to orders directory')
    parser.add_argument('--directory', '-D',  help='orders directory (default is {})'.format(configuration.get('EagleTools', 'DefaultOrdersDirectory')))
    parser.add_argument('--stamp',     '-s',                       help='version stamp (default is none)')
    parser.add_argument('--tar',       '-t',  action='store_true', help='create tar file for gerbers (default is zip)')
    parser.add_argument('--leave',     '-l',  action='store_true', help='Do not clean up unneeded files (default is to clean)')
    parser.add_argument('--verbose',   '-v',  action='store_true', help='Verbose flag')
    parser.add_argument('--force',     '-f',  action='store_true', help='Force rebuild flag')
    parser.add_argument('--project',   '-P',                       help='Project name')
    parser.add_argument('--configfile','-c',                       help='Config file (default is {})'.format(config.DefaultConfigFile))

    args = parser.parse_args()
    args.config = configuration
    
    if args.configfile is not None:
        configuration.read(args.configfile)    

    # testconfig(args)

    generate_DESCRIPTION(args)
    somethingChanged |= generateImagesFromEagle(args)
    somethingChanged |= generateGerbersFromEagle(args)

    generateFabFiles(args)

    if somethingChanged and not args.noarchive: # == default is to archive things...
        generateArchive(args)

    if somethingChanged and args.order:
        copyFiles2Order(args)   # copy Gerbers ZIP/TAR to d

if __name__ == "__main__":
    main()

