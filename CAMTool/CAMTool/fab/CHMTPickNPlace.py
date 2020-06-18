#!/usr/bin/env python3

"""
Author: John Plocher, 2019
URL:    www.SPCoast.com
License: Python Software Foundation License

Inspired by Sparkfun's CHMT ULP tutorial
(https://www.sparkfun.com/sparkx/blog/2591)

This module supports writing stand alone scripts (see eagle2chmp.py, for example)
that can be run from a Makefile without invoking eagle and running their ULP interactively
The Google Doc format is expanded and reordered from the Sparkfun original
    feel free to look at / borrow the one referenced here with the default key,
    but you will need to use your own doc if you wish to modify things :-)

  -John Plocher
   July 2018
   www.SPCoast.com

"""

__version__ = "0.1"

import CAMTool.fab.SiteConfiguration as config # local config details

import csv
import urllib.request, urllib.error, urllib.parse


SKIP       = -1
NOTFOUND   = -2

# csv file column names
tapesize   = 'Tape Size'
feedernum  = 'Feeder Number'
partname   = 'Component'
feederXoff = 'Feeder XOffset'
feederYoff = 'Feeder YOffset'
pickheight = 'PickHeight'
pickdelay  = 'PickDelay'
pullspeed  = 'PullSpeed'
pulldist   = 'Pull Distance'
placeheight= 'Place Height'
placespeed = 'Place Speed'
head       = 'Head'
rotation   = 'Part Rotation'
place      = 'Place Component'
usevacuum  = 'Check Vacuum'
usevision  = 'Use Vision'
partsizeX  = 'Size X'
partsizeY  = 'Size Y'
centroidX  = 'Centroid Correction X'
centroidY  = 'Centroid Correction Y'
aliases    = 'Aliases'
stocknotes = 'Stock Notes'
inventory  = 'Inventory Notes'
reference  = 'Used On'

options    = 'Options'

# csv file column order
idx = {}
idx[tapesize]    = 0
idx[feedernum]   = 1
idx[partname]    = 2
idx[feederXoff]  = 3
idx[feederYoff]  = 4
idx[pickheight]  = 5
idx[pickdelay]   = 6
idx[pullspeed]   = 7
idx[pulldist]    = 8
idx[placeheight]  = 9
idx[placespeed]  = 10
idx[head]        = 11
idx[rotation]    = 12
idx[place]       = 13
idx[usevacuum]   = 14
idx[usevision]   = 15
idx[partsizeX]   = 16
idx[partsizeY]   = 17
idx[centroidX]   = 18
idx[centroidY]   = 19
idx[aliases]     = 20
idx[stocknotes]  = 21
idx[inventory]   = 22
idx[reference]   = 23


# Workflow:
#    downloadFeederFile(feederfilename, GDocSheetKey):
#
#       Download a local copy of the Feeder Sheet from Google Docs
#       that contains a list of the feeders and parts loaded into them
#       on your CHMT machine:  feeders.csv
#
#    loadFeeders(feederfile)
#
#       Open feeders.csv, parse contents, create data structures, expand part aliases
#       feeder[feederName]  => { place, usevacuum, usevision }
#       component[partName] => feederName
#       Returns feeder dict and component dict
#
#    getFeederForComponent(partName, components)
#
#       get feederName (or SKIP) for a given part

def loadFeeders(feederfilename):
    feeders = {}
    components = {}

    with open(feederfilename, 'r') as feedercsv:
        feedereader = csv.reader(feedercsv)
        for row in feedereader:
            if row[idx[tapesize]] == tapesize:
                continue
            if row[idx[tapesize]] == "NoMount":
                continue
            if row[idx[tapesize]] == "Stop":
                break
            num = row[idx[feedernum]]
            if num == "":
                continue
            me = {}
            for k,v in list(idx.items()):
                me[k] = row[v]

            me[place]       = True if me[place]     == "Y" else False
            me[usevacuum]   = True if me[usevacuum] == "Y" else False
            me[usevision]   = True if me[usevision] == "Y" else False
            #  Status = 0b.0000.0ABC
            #  A = 1 = Use Vision
            #  A = 0 = No Vision
            #  B = 1 = Use Vacuum Detection
            #  B = 0 = No Vacuum Detection
            #  C = 1 = Skip placement
            #  C = 0 = Place this component
            #  Example: 3 = no place, vac, no vis
            opt = 0
            if me[usevision]:        opt |= 0x04
            if me[usevacuum]:        opt |= 0x02
            if not me[place]:        opt |= 0x01
            me[options] = opt

            feeders[num] = me

    for fidx in sorted(feeders.keys()):
        f = feeders[fidx]
        name = f[partname].lower()
        ts   = f[tapesize].lower()
        if name == '':
            continue
        if ts == "":
            continue
        if ts == "no mount":
            continue
        if ts == "stop":
            continue
        components[name] = fidx
        if f[aliases] == '':
            continue

        aliaslist = f[aliases].split(':')
        for a in aliaslist:
            if a.lower in components:
                continue
            components[a.lower()] = fidx
        # print "Alias: {} =>  {}".format(f[partname], aliaslist)
    return (feeders, components)



def downloadFeederFile(args, feederfilename, key):
    # Borrowed from SparkFun's CHMT ulp...
    # The ID from a 'Anyone with the link can view' shared level spreadsheet
    # This spreadsheet contains configurations for each different reel of components
    if key is None or key == '':
        key = args.config.get('google', 'spreadsheet_key')

    if feederfilename is None or feederfilename == '':
        feederfilename = config.defaultfeederfile
    print("Downloading feeder data from the Google ..."),

    # This is the public spreadsheet that contains all our feeder data
    # I'm too tired to use OAuth at the moment
    url = 'https://docs.google.com/spreadsheet/ccc?key=' + key + '&output=csv'
    response = urllib.request.urlopen(url)
    data = response.read()

    print("Writing to {} ...".format(feederfilename)),

    with open(feederfilename, "wb") as code:
        code.write(data)


def getFeederForComponent(partName, components):
    pn = partName.lower()
    if pn not in components:
        return SKIP
    return components[pn]


1;
