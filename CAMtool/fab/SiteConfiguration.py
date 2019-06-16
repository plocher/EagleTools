#!/usr/bin/python

DefaultOrdersDirectory = '/Users/plocher/Dropbox/eagle/Seeed-Orders/CurrentOrder'

spreadsheet_key   = '1HuY1-9Z5yyQwUiivPqE5rH7m6A_Cvw6qmvkwXvpyZ-k'  # - this is the default public key for John's
                                                                    # feeder config Google Sheet
defaultBOMdir     = '/Users/plocher/Dropbox/eagle/BOMs/'
defaultDPVdir     = '/Users/plocher/Dropbox/eagle/DPVs/'
eagle2chmt        = "/Users/plocher/Dropbox/eagle/EagleTools/CAMtool/eagle2chmt.py"
eagle2svg         = "/Users/plocher/Dropbox/eagle/EagleTools/CAMtool/eagle2svg.py"
eagle2bom         = "/Users/plocher/Dropbox/eagle/EagleTools/CAMtool/eagle2bom.py"
defaulteaglerc    = '/Users/plocher/.eaglerc'
defaultfeederfile = './feeders.csv'

EAGLEAPP          = '/Applications/EAGLE-7.7.0/EAGLE.app/Contents/MacOS/EAGLE'

# EagleCAD Layers of interest for images
D_SCHEMATIC       = "ALL -PINS"
D_NORMAL          = "   NONE 1 16 17 18    20 21    23   25   27         44 45 46 47 48 49 51     101 102 104"
D_BSILK           = "   NONE      17 18    20    22    24         28     44 45 46 47          52"
D_TSILK           = "   NONE      17 18    20 21         25   27     29        46       49"

