Making a panelized PCB design in EagleCAD 7.7
=========================================


  * In order for these tools to work for all your projects, EageCad needs to be able to find these ulp, scr and lbr files.  By default, Eagle's library is part of the Eagle installation package, and should be treated as "read-only" so that upgrades don't overwrite/lose your changes; this means you should set up your own script library (and the rest...) as part of your eagle workspace.

  * I cloned a copy of this repo on the same filesystem as my EagleCad projects workspace, and added the resulting paths to EagleCad's controlpanel OPTIONS->DIRECTORIES...

  * Set up your own custom directory structure in the Eagle Control Panel, and add your desired directories to OPTIONS->DIRECTORIES.
The order matters - put your directory first, before the one in $EAGLEDIR, to make EagleCad look for your custom scripts before it looks for the  Default ones:

    * Directories.Scr = "$HOME/Dropbox/EagleTools/scr:$HOME/Dropbox/eagle/library/scr:$EAGLEDIR/scr"
    * Directories.Cam = "$HOME/Dropbox/EagleTools/cam:$HOME/Dropbox/eagle/library/cam:$EAGLEDIR/cam"
    * Directories.Dru = "$HOME/Dropbox/EagleTools/dru:$HOME/Dropbox/eagle/library/dru:$EAGLEDIR/dru"
    * Directories.Lbr = "$HOME/Dropbox/EagleTools/parts:$HOME/Dropbox/eagle/library/lib:$EAGLEDIR/lbr"
    * Directories.Ulp = "$HOME/Dropbox/EagleTools/ulp:$HOME/Dropbox/eagle/library/ulp:$EAGLEDIR/ulp"
    * Directories.Epf = "$HOME/Dropbox/eagle"
    * Directories.Doc = "$EAGLEDIR/doc"

      * (Windows uses a ';' semicolon between directory names, Mac and Linux (as above) use a ':' colon...)



Save (or merge) scr/eagle.scr to the top of your Eagle Projects directory (as defined in the Eagle Control Panel's OPTIONS->DIRECTORIES->PROJECTS setting).  The important bits are the menu settings to invoke the various ULPs.

Add ulp/make-panel.ulp to your OPTIONS->DIRECTORIES->User Languane Programs directory

Add the SPCoast*.cam files to your OPTIONS->DIRECTORIES->CAM Jobs directory


1. Before you can panelize a design, you need to have a singleton design to replicate.

Create such a design, using Eagle's schematic and board editors, with the following design rules:
  * Use layer 20 (Dimension layer) to mark the rectangular outline of the design.  Complex board outlines are much harder to panelize because they can't be delimited by simple V-Score actions on the Milling layer, and so are not candidates for these instructions.
  * Put part names and values on the tNames and tValues (or bNames and bValues, as needed)
  * Ensure any/all polygon fill planes are 5 mil away from the board edge to leave room for the V-Score between boards (i.e., a ground plane polygon with a 20mil Width needs to be at least 15mil (20mil / 2 + 5mil) from the board edge)
  * clean out unused layers

     layer ?? -100;  layer ?? -101;  layer ?? -102;  layer ?? -103;  layer ?? -104;  layer ?? -105;  layer ?? -106;  layer ?? -107;  layer ?? -108;  layer ?? -109;  layer ?? -110;  layer ?? -111;  layer ?? -112;  layer ?? -113;  layer ?? -114;  layer ?? -115;  layer ?? -116;  layer ?? -117;  layer ?? -118;  layer ?? -119;  layer ?? -120;  layer ?? -121;  layer ?? -122;  layer ?? -123;  layer ?? -124;  layer ?? -125;  layer ?? -126;  layer ?? -127;  layer ?? -128;  layer ?? -129;  layer ?? -130;  layer ?? -131;  layer ?? -132;  layer ?? -133;  layer ?? -134;  layer ?? -135;  layer ?? -136;  layer ?? -137;  layer ?? -138;  layer ?? -139;  layer ?? -140;  layer ?? -141;  layer ?? -142;  layer ?? -143;  layer ?? -144;  layer ?? -145;  layer ?? -146;  layer ?? -147;  layer ?? -148;  layer ?? -149;  layer ?? -150;  layer ?? -151;  layer ?? -152;  layer ?? -153;  layer ?? -154;  layer ?? -155;  layer ?? -156;  layer ?? -157;  layer ?? -158;  layer ?? -159;  layer ?? -160;  layer ?? -161;  layer ?? -162;  layer ?? -163;  layer ?? -164;  layer ?? -165;  layer ?? -166;  layer ?? -167;  layer ?? -168;  layer ?? -169;  layer ?? -170;  layer ?? -171;  layer ?? -172;  layer ?? -173;  layer ?? -174;  layer ?? -175;  layer ?? -176;  layer ?? -177;  layer ?? -178;  layer ?? -179;  layer ?? -180;  layer ?? -181;  layer ?? -182;  layer ?? -183;  layer ?? -184;  layer ?? -185;  layer ?? -186;  layer ?? -187;  layer ?? -188;  layer ?? -189;  layer ?? -190;  layer ?? -191;  layer ?? -192;  layer ?? -193;  layer ?? -194;  layer ?? -195;  layer ?? -196;  layer ?? -197;  layer ?? -198;  layer ?? -199;  layer ?? -200;  layer ?? -201;  layer ?? -202;  layer ?? -203;  layer ?? -204;  layer ?? -205;  layer ?? -206;  layer ?? -207;  layer ?? -208;  layer ?? -209;  layer ?? -210;  layer ?? -211;  layer ?? -212;  layer ?? -213;  layer ?? -214;  layer ?? -215;  layer ?? -216;  layer ?? -217;  layer ?? -218;  layer ?? -219;  layer ?? -220;  layer ?? -221;  layer ?? -222;  layer ?? -223;  layer ?? -224;  layer ?? -225;  layer ?? -226;  layer ?? -227;  layer ?? -228;  layer ?? -229;  layer ?? -230;  layer ?? -231;  layer ?? -232;  layer ?? -233;  layer ?? -234;  layer ?? -235;  layer ?? -236;  layer ?? -237;  layer ?? -238;  layer ?? -239;  layer ?? -240;  layer ?? -241;  layer ?? -242;  layer ?? -243;  layer ?? -244;  layer ?? -245;  layer ?? -246;  layer ?? -247;  layer ?? -248;  layer ?? -249;  layer ?? -250;  layer ?? -251;  layer ?? -252;  layer ?? -253;  layer ?? -254; 
layer ?? -255;

Save this singleton project.  For my projects, I create a directory structure for each project, with the top level bearing the name of the project and subdirectories for each version: 

   Detector/1.0/Detector.sch<br>
   Detector/1.0/Detector.brd

2. Invoke the Eagle-provided ULP that copies the [tb]Names layers content to new unused ones (125 126, _tNames, _bNames).  
Press OK in the popup dialog; it doesn't look like it does anything, but a look at the layers list / content will show the new layers with the old content copied into them:

   run panelize
   DISPLAY -25 -27

3. Save the EagleCad Design (File / Save)
4. Invoke the (new) make-panel ULP script from the singleton's BRD editor.  Its popup asks for the number of copies it should create, in a 2-dimensional array.
This ULP creates a SCRipt file that will be used in the next steps to create a panelized design.  This SCRipt defaults to the same name as the singleton design, byt with a ".scr" extention.

   run make-board

5. Start a new empty board design:
  * File->New (click "yes" to the warning message...)

6. Run the SCRipt we created earlier to create a panelized version of the singleton board

   SCRIPT Detector_array

7. Save this design as Detector_array.brd in the Detector/1.0/ directory.

The layer 20 DIMension lines in the original design are now on the new Hidden layer 101, and there are Milling layer 46 v-score lines and instructions for the board fab that will be used to split the panel into its subcomponent pieces.
You will want to add a new layer20 DIMension box around the outside of the panel, and delete any unnecessary layer 46 Milling V-Scores.

8. The final step is to create Gerber files from this panel design.  Because you will want all the silkscreen part names to be the same on every board, change all references to layer 25 to the new layer 125, and 27 to 127 in your CAM job file before you run it.  The SPCoast Panel CAM job files in this project do this.


----
EagleCAD 9.* changed the "WIRE" command to "LINE"; the make-panel.ulp program uses "WIRE".  AutoDesk may, at some time, start genrating errors when the WIRE command is used; if so, the fix is easy.  Unfortunately, that fix would break older versions that don't know about "LINE"...

