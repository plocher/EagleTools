"""
This should move into a configparser structure..
"""
__version__ = "0.1"

class Configuration(object):
    def __init__(self, program):
        self.program                     = program
        self.lastupload                  = ".uploaded"

        # source tree locations
        self.sourceDirIsEagle            = "/Users/jplocher/Dropbox/eagle/"
        self.sourceDirIsControlPoint     = "/Users/jplocher/Dropbox/workspace/ArduinoPoint/"
        self.sourceDirIsArduino          = "/Users/jplocher/Dropbox/Arduino/"
        self.sourceDirIsArduinoLibrary   = "/Users/jplocher/Dropbox/Arduino/libraries"
        self.sourceDirIsCAD              = "/Users/jplocher/Dropbox/CAD/"
        self.sourceDirIsScript           = "/Users/jplocher/Dropbox/Scripts/"
        self.sourceDirIsWikiDoc          = "/Users/jplocher/Dropbox/WikiDocs/"
        self.sourceDirIsExpressPCB       = "/Users/jplocher/Dropbox/ExpressPCB/Published/"
        
        self.ARDUINO_LIB_HOME            = "/Applications/Arduino.app/Contents/Java/hardware/arduino/avr/libraries/"
        self.ARDUINO_USER_LIB_HOME       = "/Users/jplocher/Dropbox/Arduino/libraries/"


        #self.JEKYLL_GITHUB_PUBLISH_DIR   = None
        #self.JEKYLL_PUBLISH_PAGES_DIR    = "docs/pages/"       # relative to parent dir of project..
        #self.JEKYLL_PUBLISH_VERSIONS_DIR = "docs/_versions/"

        self.JEKYLL_PUBLISH_PAGES_DIR    = "pages/"            # relative to JEKYLL_GITHUB_PUBLISH_DIR
        self.JEKYLL_URL_PAGES_DIR        = "/pages/"           # absolute URL base for project pages

        self.JEKYLL_GITHUB_PUBLISH_DIR_EAGLE   = "/Users/jplocher/Dropbox/eagle/SPCoast.github.io/" # or None if local to repo
        self.JEKYLL_LOCAL_PUBLISH_DIR_EAGLE    = "_versions/"
        self.JEKYLL_URL_PUBLISH_DIR_EAGLE      = "/versions/"        # ... for project versions

        self.JEKYLL_GITHUB_PUBLISH_DIR_ARDUINO = "/Users/jplocher/Dropbox/eagle/SPCoast.github.io/" # or None if local to repo
        self.JEKYLL_LOCAL_PUBLISH_DIR_ARDUINO  = "_sketches/"
        self.JEKYLL_URL_PUBLISH_DIR_ARDUINO    = "/sketches/"        # ... for project versions
