Setting defaults
================

The SCRIPT file eagle.scr - if it exists in the project directory or in the script path - is executed each time a new drawing is loaded into an editor window (or when the drawing type is changed in a library).

In order for this to work for all your projects, this file should be installed in EageCad's script library.  By default, Eagle's library is part of the Eagle installation package, and should be treated as "read-only" so that upgrades don't overwrite/lose your changes; this means you should set up your own script library (and the rest...) as part of your eagle workspace.

For my use, I set this all up in a shared Dropbox folder; you don't need to use cloud storage, but it really makes it convenient when you use multiple computers....  I use ~/Dropbox/eagle as the root for all my EagleCad efforts, with a "library" subdir for all these eagle scripts, ULPs, CAM files and, of course, my own customized library of parts.

To set up your own custom directory structure, go to the Eagle Control Panel, and add your desired directories to OPTIONS->DIRECTORIES.
The order matters - put your directory first, before the one in $EAGLEDIR, to make EagleCad look for your custom scripts before it looks for the  Default ones:

  * Directories.Scr = "$HOME/Dropbox/eagle/library/scr:$EAGLEDIR/scr"
  * Directories.Cam = "$HOME/Dropbox/eagle/library/cam:$EAGLEDIR/cam"
  * Directories.Dru = "$HOME/Dropbox/eagle/library/dru:$EAGLEDIR/dru"
  * Directories.Lbr = "$HOME/Dropbox/eagle/library/lib:$EAGLEDIR/lbr"
  * Directories.Ulp = "$HOME/Dropbox/eagle/library/ulp:$EAGLEDIR/ulp"
  * Directories.Epf = "$HOME/Dropbox/eagle"
  * Directories.Doc = "$EAGLEDIR/doc"

(Windows uses a ';' semicolon between directory names, Mac and Linux (as above) use a ':' colon...)


