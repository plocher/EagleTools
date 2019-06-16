CAM files for use with EagleCAD
===============================
These CAM jobs create the files needed to have a PCB created.  
 When run as a CAM Processor job in EAGLE-CAD, they will produce a set of files that, when zipped together, 
 are everything you need to have a PCB made at nearly any fab house.


  * SPCoast-gerb274x-PanelSilk.cam
    * For use with panelized designs that have component names copied to the _tNames layer 125.

  * SPCoast-gerb274x-Singleton.cam
    * For use with singleton designs that have component names in the tNames layer 25. 

  * SPCoast-gerb274x-Values.cam
    *  For use with singleton or panelized designs, when component values are desired INSTEAD of component names. 

  * SPCoast-gerb274x-noPartInfo.cam
    *  For use with Singleton or panelized designs that do not want component names OR values to show up on the PCB. 

You should get 10x RS274-x format gerber files:</b>
  * Top Layer: pcbname.GTL
  * Silk Top:  pcbname.GTO
  * SolderMask Top: pcbname.GTS
  * SMD paste Top: pcbname.GTP
  * Bottom Layer: pcbname.GBL
  * Silk Bottom: pcbname.GBO
  * SolderMask Bottom: pcbname.GBS
  * SMD paste Bottom: pcbname.GBP
  * V-Scores/Holes: pcbname.GML
  * NC Drill file:pcbname.TXT


