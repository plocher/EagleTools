"""
This should move into a configparser structure..
"""
__version__ = "0.1"

class Configuration(object):
    def __init__(self, program):
        self.program                     = program
        self.lastupload                  = ".uploaded"

        # source tree locations
        self.sourceDirIsEagle            = "/Users/plocher/Dropbox/eagle/"
        self.sourceDirIsControlPoint     = "/Users/plocher/Dropbox/workspace/ArduinoPoint/"
        self.sourceDirIsArduino          = "/Users/plocher/Dropbox/Arduino/"
        self.sourceDirIsArduinoLibrary   = "/Users/plocher/Dropbox/Arduino/libraries"
        self.sourceDirIsCAD              = "/Users/plocher/Dropbox/CAD/"
        self.sourceDirIsScript           = "/Users/plocher/Dropbox/Scripts/"
        self.sourceDirIsWikiDoc          = "/Users/plocher/Dropbox/WikiDocs/"
        self.sourceDirIsExpressPCB       = "/Users/plocher/Dropbox/ExpressPCB/Published/"
        
        self.ARDUINO_LIB_HOME            = "/Applications/Arduino.app/Contents/Java/hardware/arduino/avr/libraries/"
        self.ARDUINO_USER_LIB_HOME       = "/Users/plocher/Dropbox/Arduino/libraries/"


        #self.JEKYLL_GITHUB_PUBLISH_DIR   = None
        #self.JEKYLL_PUBLISH_PAGES_DIR    = "docs/pages/"       # relative to parent dir of project..
        #self.JEKYLL_PUBLISH_VERSIONS_DIR = "docs/_versions/"

        self.JEKYLL_PUBLISH_PAGES_DIR    = "pages/"            # relative to JEKYLL_GITHUB_PUBLISH_DIR
        self.JEKYLL_URL_PAGES_DIR        = "/pages/"           # absolute URL base for project pages

        self.JEKYLL_GITHUB_PUBLISH_DIR_EAGLE   = "/Users/plocher/Dropbox/eagle/SPCoast.github.io/" # or None if local to repo
        self.JEKYLL_LOCAL_PUBLISH_DIR_EAGLE    = "_versions/"
        self.JEKYLL_URL_PUBLISH_DIR_EAGLE      = "/versions/"        # ... for project versions

        self.JEKYLL_GITHUB_PUBLISH_DIR_ARDUINO = "/Users/plocher/Dropbox/eagle/SPCoast.github.io/" # or None if local to repo
        self.JEKYLL_LOCAL_PUBLISH_DIR_ARDUINO  = "_sketches/"
        self.JEKYLL_URL_PUBLISH_DIR_ARDUINO    = "/sketches/"        # ... for project versions
