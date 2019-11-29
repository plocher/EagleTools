
Python tools to manipulate EagleCAD files
=========================================

* eagle2CAM.py    - A Command Line tool to create Gerbers and other artifacts from an Eagle BRD file.
   * archives the current SCH/BRD files in a datestamped Archive directory,
   * generates a ZIP (optional TAR) file of the gerbers for easy uploading,
   * generates image files of the board and schematic
   * copies the ZIP file to a Current Orders directory to make it harder to forget to order new versions of a board
   * cleans up unnecessary temp files

* eagle2bom.py
   * Create a bill of materials (aka partslist) from a EagleCAD BRD file

* eagle2chmt.py
   * Create a pick-and-place command file for a CharmHigh SMT Placement Machine and a Google Docs spreadsheet
   * Inspired by Nate\'s [SparkFun blog posts](https://www.sparkfun.com/sparkx/blog/2586)

* eagle2svg.py
   * Create SVG images of a board

* eagleLib2TOC.py
   * (in progress) Create a Library Table of Contents from an EagleCAD Library, suitable for inclusion on a MediaWiki web page.
