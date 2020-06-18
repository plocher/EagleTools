#!/usr/bin/env python3
# test program for jekyll content generation


import argparse
from pathlib import Path
import io
import os
import sys
from git import Git
import re
#import configparser




# test.py
print(__name__)

try:
    # Trying to find module in the parent package
    from jekyll.Configuration import Configuration as Configuration
    from jekyll.CopyFile import CopyFile as CopyFile
    #print("Relative import OK")
except ImportError:
    #print('Relative import failed')

    try:
        # Trying to find module on sys.path
        import CAMTool.jekyll.Configuration as Configuration
        import CAMTool.jekyll.CopyFile as CopyFile
        #print("Absolute import OK")

    except ModuleNotFoundError:
        print('Absolute import failed: Relative import failed: [CAMTool.]jekyll.* Module not found')



def sorted_nicely( l ):
    """ Sorts the given iterable in the way that is expected.
 
    Required arguments:
    l -- The iterable to be sorted.
 
    """
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key = alphanum_key)


def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

class Location(object):
    def __init__(self):
        self.handlers = {}
        self.dirs = {}
        
    def add(self, tag, srcdir, handler):
        self.handlers[tag] = handler
        self.dirs[srcdir] = tag
    
    def find(self, dir):
        for d in self.dirs:
            if d in dir:
                return (d, self.dirs[d])
        return (None, None)
    
    def run(self, args):
        return self.handlers[args.projecttype](args)

def processTODO(args):
    print("TODO()")
    return ""

def processArduino(args):
    #repo = Git("./")

    all_files = os.listdir(".")
    #tag = repo.describe()
    tag="1.0"
    #print("Tag={}".format(tag))

    #processArduino(args, tag, args.project, all_files)




    if args.verbose or args.show:
        print("processArduino({})".format(args.project))

    outfilename = '{project}.md'.format(project=args.project)
    outfilename = os.path.join(args.conf.JEKYLL_PUBLISH_PAGES_DIR, outfilename)

    pubdir = args.conf.JEKYLL_GITHUB_PUBLISH_DIR_EAGLE
    if pubdir:
        outfilename = os.path.join(pubdir, outfilename)

    # check if any destination dirs need to be created
    d = outfilename
    d = os.path.dirname(d)

    if not os.path.isdir(d):
        if args.verbose or args.show:
            print("+mkdir -p {dir}".format(dir=d))
        if not args.show:
            os.makedirs(d)

    if args.show:
        output = io.StringIO()
    else:
        output = open(outfilename, "w")

    need_tagline = True
    need_overview = True
    need_tags = True
    need_layout = True

    # defaults
    tagline  = 'description not provided'
    overview = '    '

    output.write('---\n')
    output.write('isarduino: true\n')
    output.write('sidebar: spcoast_sidebar\n')
    output.write('title: {}\n'.format(args.project))
    output.write('project: {}\n'.format(args.project))

    if os.path.isfile("INFO"):
        #print("use INFO...");
        if os.path.isfile("INFO"):
            with open("INFO", 'r') as content_file:
                for line in content_file:
                    if line.startswith("title:") or line.startswith("project:"):
                        continue
                    if line.startswith("tags:"):
                        need_tags = False
                    if line.startswith("layout:"):
                        need_layout = False
                    if line.startswith("tagline:"):
                        need_tagline = False
                    if line.startswith("overview:"):
                        need_overview = False

                    output.write(line)
    if need_tagline or need_overview:
        if os.path.isfile('DESCRIPTION'):  # exists...
            #print("use DESCRIPTION")
            with open('DESCRIPTION', 'r') as description_file:
                description = description_file.readlines()
                if description:  # ... and has content
                    tagline = description[0][:-1]
                    need_tagline = False
                if len(description) > 1:
                    need_overview = False
                    overview = ''
                    raw = ''
                    skipfirst = True
                    for s in description:
                        if skipfirst:
                            skipfirst = False
                            continue
                        overview = overview + '    ' + s
                        raw = raw + s
                    overview = overview[:-1]  # remove the final newline (gets added back when output later)
        else:
            pass
            # print("use Defaults...")

    if need_layout:
        output.write('layout: arduino\n')
    if need_tags:
        output.write('tags: [SPCoast, arduino]\n')

    output.write('tagline: {}\n'.format(tagline))
    output.write('overview: >\n{}\n'.format(overview))

    sep = 'images:\n'
    for filename in sorted_nicely(all_files):
        root, ext = os.path.splitext(filename)
        if ext.lower() in ['.png', '.jpg', '.gif']:
            args.queue.copy(args.project, None, filename)
            tag = root

            s = "{sep}  - image_path: {dir}{project}/{filename}\n    title: {tag}\n"
            output.write(s.format(sep=sep, dir=args.conf.JEKYLL_URL_PUBLISH_DIR_ARDUINO,
                                  project=args.project,
                                  filename=filename,
                                  tag=tag))
            sep = ""
    sep = 'artifacts:\n'
    for filename in sorted_nicely(all_files):
        # print("parent artifact: file: {}".format(filename))
        skip = False
        root, ext = os.path.splitext(filename)

        if (ext is None or ext == ''):
            #print("   ... skipping - no extension")
            skip = True
        if ext.lower() in ['.png', '.jpg', '.gif', '.md', '.swp']:
            skip = True
        if ext.lower() in ['.b#1', '.b#2', '.b#3', '.b#4', '.b#5', '.b#6', '.b#7', '.b#8', '.b#9']:
            skip = True
        if ext.lower() in ['.s#1', '.s#2', '.s#3', '.s#4', '.s#5', '.s#6', '.s#7', '.s#8', '.s#9']:
            skip = True

        if not skip:
            args.queue.copy(args.project, None, filename)
            pretext = 'download'
            tag = root
            posttext = ''

            if ext.lower() == '.pdf':
                posttext = 'Documentation'
                tag=filename
            elif ext.lower() == '.ino':
                posttext = 'Arduino Sketch'
                tag = filename
            elif ext.lower() == '.pde':
                posttext = 'Arduino Sketch'
                tag = filename
            elif ext.lower() == '.cpp':
                posttext = 'Arduino Sketch C++ helper code'
                tag = filename
            elif ext.lower() == '.c':
                posttext = 'Arduino Sketch C helper code'
                tag = filename
            elif ext.lower() == '.h':
                posttext = 'Arduino Sketch header file'
                tag = filename
            elif ext.lower() == '.docx':
                posttext = 'Word Document'
                tag=filename
            elif ext.lower() == '.xlsx':
                posttext = 'Spreadsheet'
                tag=filename
            #print("   ... ADD: {} {}".format(tag, posttext))

            s = "{sep}  - path: {dir}{project}/{filename}\n"
            s = s + "    tag: {tag}\n    type: {pretext}\n    post: {posttext}\n"
            s = s.format(sep=sep, dir=args.conf.JEKYLL_URL_PUBLISH_DIR_ARDUINO,
                                  project=args.project,
                                  pretext=pretext,
                                  tag=tag,
                                  posttext=posttext,
                                  filename=filename,
                                  file=root)
            output.write(s)
            sep = ""
    # TODO: Add links to any source files - followed by their syntax highlighted content
    # output.write('permalink: {}.html\n'.format(args.project))
    output.write('---\n')

    if os.path.isfile('doc.md'):    # first!
        with open("doc.md", 'r') as content_file:
            output.write("\n")
            output.write("## {}\n\n".format("Documentation"))
            output.write(content_file.read())

    for filename in sorted_nicely(all_files):
        skip = False
        root, ext = os.path.splitext(filename)
        if ext.lower() in ['.md']:
            if filename == "doc.md":
                skip = True
            if filename == "README.md":         # only for github
                skip = True
            if filename == "LICENSE.md":        # last
                skip = True
            if filename == "LICENSE":           # skip verbose version
                skip = True
            if not skip:
                with open(filename, 'r') as content_file:
                    output.write("\n")
                    output.write("## {}\n\n".format(root))
                    output.write(content_file.read())

        elif ext.lower() in ['.ino', '.pde', '.h', '.c', '.cpp']:
            with open(filename, 'r') as content_file:
                output.write("\n")
                output.write("## {}\n\n~~~ cpp\n".format(root))
                output.write(content_file.read())
                output.write(" \n~~~\n")

        elif ext.lower() in ['.py']:
            with open(filename, 'r') as content_file:
                output.write("\n")
                output.write("## {}\n\n~~~ python\n".format(root))
                output.write(content_file.read())
                output.write(" \n~~~\n")


    if os.path.isfile('LICENSE.md'):
        # Add LICENSE file at end
        with open("LICENSE.md", 'r') as content_file:
            output.write("\n\n----\n")
            output.write("\n")
            output.write(content_file.read())

    if args.show:
        content = output.getvalue()
        print('# create {}'.format(outfilename))
        if args.verbose:
            print('====Contents====')
            print(content)
            print('================')
    else:
        output.close()

    return ""

def processEagleParent(args, projectname, version, all_files):
    if args.verbose or args.show:
        print("processEagleParent({})".format(projectname))

    outfilename = '{project}.md'.format(project=projectname)
    outfilename = os.path.join(args.conf.JEKYLL_PUBLISH_PAGES_DIR, outfilename)
    # parent pages go into .../pages
    # child pages go into .../_versions/VERSION/

    pubdir = args.conf.JEKYLL_GITHUB_PUBLISH_DIR_EAGLE
    if pubdir:
        outfilename = os.path.join(pubdir, outfilename)

    # check if any destination dirs need to be created
    d = outfilename
    d = os.path.dirname(d)

    if not os.path.isdir(d):
        print("+mkdir -p {dir}".format(dir=d))
        if not args.show:
            os.makedirs(d)

    if args.show:
        output = io.StringIO()
    else:
        output = open(outfilename, "w")

    need_tagline = True
    need_overview = True
    need_tags = True
    need_layout = True
    need_graphic = True

    # defaults
    tagline  = 'description not provided'
    overview = '    '

    output.write('---\n')
    output.write('iseagle: true\n')
    output.write('sidebar: spcoast_sidebar\n')
    output.write('title: {}\n'.format(projectname))
    output.write('project: {}\n'.format(projectname))

    if os.path.isfile("INFO"):
        #print("use INFO...");
        if os.path.isfile("INFO"):
            with open("INFO", 'r') as content_file:
                for line in content_file:
                    if line.startswith("title:") or line.startswith("project:"):
                        continue
                    if line.startswith("tags:"):
                        need_tags = False
                    if line.startswith("image_path:"):
                        need_graphic = False
                    if line.startswith("layout:"):
                        need_layout = False
                    if line.startswith("tagline:"):
                        need_tagline = False
                    if line.startswith("overview:"):
                        need_overview = False

                    output.write(line)
    if need_tagline or need_overview:
        if os.path.isfile('DESCRIPTION'):  # exists...
            #print("use DESCRIPTION")
            with open('DESCRIPTION', 'r') as description_file:
                description = description_file.readlines()
                if description:  # ... and has content
                    tagline = description[0][:-1]
                    need_tagline = False
                if len(description) > 1:
                    need_overview = False
                    overview = ''
                    raw = ''
                    skipfirst = True
                    for s in description:
                        if skipfirst:
                            skipfirst = False
                            continue
                        overview = overview + '    ' + s
                        raw = raw + s
                    overview = overview[:-1]  # remove the final newline (gets added back when output later)
        else:
            pass
            # print("use Defaults...")

    if need_layout:
        output.write('layout: eagle\n')
    if need_graphic:
        graphicname = "{project}.top.brd.png".format(version=version, project=projectname)
        graphicname2 = "{project}-{version}.top.brd.png".format(version=version, project=projectname)
        if os.path.isfile(graphicname):
            output.write('image_path: {version}/{graphicname}\n'.format(version=version, graphicname=graphicname2))
        else:
            output.write('Ximage_path: {version}/{graphicname}\n'.format(version=version, graphicname=graphicname2))
    if need_tags:
        output.write('tags: [SPCoast, eagle]\n')

    output.write('tagline: {}\n'.format(tagline))
    output.write('overview: >\n{}\n'.format(overview))

    sep = 'images:\n'
    for filename in all_files:
        skip = False
        for ending in ['sch.png', '.brd.png', '.top.brd.png', '.bot.brd.png']:
            if filename.endswith(ending):
                skip=True
        if not skip:
            root, ext = os.path.splitext(filename)
            if ext.lower() in ['.png', '.jpg', '.gif']:
                args.queue.copy(projectname, None, filename)
                tag = root

                s = "{sep}  - image_path: {dir}{project}/{filename}\n    title: {tag}\n"
                output.write(s.format(sep=sep, dir=args.conf.JEKYLL_URL_PUBLISH_DIR_EAGLE,
                                      project=projectname,
                                      filename=filename,
                                      tag=tag))
                sep = ""
    sep = 'artifacts:\n'
    for filename in sorted_nicely(all_files):
        #print("parent artifact: file: {}".format(filename))
        skip = False
        root, ext = os.path.splitext(filename)

        if (ext is None or ext == ''):
            #print("   ... skipping - no extension")

            skip = True

        if ext.lower() in ['.gbl', '.gbo', '.gbp', '.gbs', '.gko',
                           '.gtl', '.gto', '.gtp', '.gts', '.gml', '.txt',
                           '.md',  '.dri', '.gpi', '.svg', '',
                           '.png', '.jpg', '.sch', '.dpv']:
            #print("   ... skipping - ext {} matches".format(ext))
            skip = True
        if ext.lower() in ['.b#1', '.b#2', '.b#3', '.b#4', '.b#5', '.b#6', '.b#7', '.b#8', '.b#9']:
            skip = True
        if ext.lower() in ['.s#1', '.s#2', '.s#3', '.s#4', '.s#5', '.s#6', '.s#7', '.s#8', '.s#9']:
            skip = True

        for ending in ['.eagle.tar', '.eagle.zip', '.gerbers.tar', '.gerbers.zip', '.parts.csv']:
            if filename.lower().endswith(ending):
                #print("   ... skipping - end {} matches".format(ending))
                skip = True

        for name in ['{}.brd', '{}_array.brd']:
            name = name.format(projectname)
            if filename == name:
                #print("   ... skipping - name {} matches".format(name))
                skip = True

        if not skip:
            args.queue.copy(projectname, None, filename)
            pretext = 'download'
            tag = root
            posttext = ''

            if ext.lower() == '.pdf':
                posttext = 'Documentation'
                tag=filename
            elif ext.lower() == '.ino':
                posttext = 'Arduino Sketch'
                tag = filename
            elif ext.lower() == '.scr':
                posttext = 'Eagle SCRipt'
                tag = filename
            elif ext.lower() == '.brd':
                posttext = 'Eagle PCB file'
                tag = filename
            elif ext.lower() == '.xlsx':
                posttext = 'Spreadsheet'
                tag=filename
            #print("   ... ADD: {} {}".format(tag, posttext))

            s = "{sep}  - path: {dir}{project}/{filename}\n"
            s = s + "    tag: {tag}\n    type: {pretext}\n    post: {posttext}\n"
            s = s.format(sep=sep, dir=args.conf.JEKYLL_URL_PUBLISH_DIR_EAGLE,
                                  project=projectname,
                                  pretext=pretext,
                                  tag=tag,
                                  posttext=posttext,
                                  filename=filename,
                                  file=root)
            output.write(s)
            sep = ""
    # TODO: Add links to any source files - followed by their syntax highlighted content
    # output.write('permalink: {}.html\n'.format(projectname))
    output.write('---\n')

    if os.path.isfile('doc.md'):    # first!
        content_file = open('doc.md', 'r')
        if content_file:
            output.write("\n")
            output.write("## {}\n\n".format("Documentation"))
            output.write(content_file.read())
            content_file.close()

    for filename in sorted_nicely(all_files):
        root, ext = os.path.splitext(filename)
        if ext.lower() in ['.md']:
            if filename.lower == "doc.md":
                continue
            if filename == "README.md":         # only for github
                continue
            if filename == "LICENSE.md":        # last
                continue
            if filename.endswith(".bom.md"):    # handled in child tab...
                continue
            content_file = open(filename, 'r')
            if content_file:
                output.write("\n")
                output.write("## {}\n\n".format(root))
                output.write(content_file.read())
                content_file.close()

        # show Arduino sketches unless already wrapped in a .md file
        elif ext.lower() in ['.ino'] and not os.path.isfile("{}.md".format(filename)):
            content_file = open(filename, 'r')
            if content_file:
                output.write("\n")
                output.write("## {}\n\n~~~ cpp\n".format(root))
                output.write(content_file.read())
                output.write(" \n~~~\n")
                content_file.close()


    if os.path.isfile('LICENSE.md'):
        # Add LICENSE file at end
        content_file = open("LICENSE.md", 'r')
        if content_file:
            output.write("\n")
            output.write("\n")
            output.write(content_file.read())
            content_file.close()

    if args.show:
        content = output.getvalue()
        print('# create {}'.format(outfilename))
        if args.verbose:
            print('====Contents====')
            print(content)
            print('================')
    else:
        output.close()


def processEagleChild(args, projectname, version, all_files):
    if args.verbose or args.show:
        print("processEagleChild({})".format(version))

    outfilename = '{version}.md'.format(version=version)
    outfilename = os.path.join(projectname, outfilename)
    outfilename = os.path.join(args.conf.JEKYLL_LOCAL_PUBLISH_DIR_EAGLE, outfilename)  # _versions/xxx

    pubdir = args.conf.JEKYLL_GITHUB_PUBLISH_DIR_EAGLE
    if pubdir:
        outfilename = os.path.join(pubdir, outfilename)
    else:
        outfilename = os.path.join(".", outfilename)

    project_state = "unknown"

    # check if any destination dirs need to be created
    d = outfilename
    d = os.path.dirname(d)

    if not os.path.isdir(d):
        print("+mkdir -p {dir}".format(dir=d))
        if not args.show:
            os.makedirs(d)

    if args.show:
        output = io.StringIO()
    else:
        output = open(outfilename, "w")

    output.write('---\n')
    output.write('iseagle: true\n')
    output.write('layout: eagle\n')
    output.write('sidebar: spcoast_sidebar\n')
    output.write('project: {}\n'.format(projectname))
    output.write('title: {}\n'.format(version))


    need_tagline = True
    need_overview = True

    # defaults
    tagline  = 'description not provided'
    overview = '    '

    if os.path.isfile("INFO"):
        #print("use INFO...");
        if os.path.isfile("INFO"):
            with open("INFO", 'r') as content_file:
                for line in content_file:
                    if line.startswith("title:") or line.startswith("project:"):
                        continue
                    if line.startswith("tagline:"):
                        need_tagline = False
                    if line.startswith("overview:"):
                        need_overview = False
                    output.write(line)
    else:
        output.write('status: {}\n'.format(project_state))

    if need_tagline or need_overview:
        if os.path.isfile('DESCRIPTION'):  # exists...
            #print("use DESCRIPTION")
            with open('DESCRIPTION', 'r') as description_file:
                description = description_file.readlines()
                if description:  # ... and has content
                    tagline = description[0][:-1]
                    need_tagline = False
                if len(description) > 1:
                    need_overview = False
                    overview = ''
                    raw = ''
                    skipfirst = True
                    for s in description:
                        if skipfirst:
                            skipfirst = False
                            continue
                        overview = overview + '    ' + s
                        raw = raw + s
                    overview = overview[:-1]  # remove the final newline (gets added back when output later)
        else:
            pass
            # print("use Defaults...")

    output.write('tagline: {}\n'.format(tagline))
    output.write('overview: >\n{}\n'.format(overview))

    sep = 'images:\n'
    for filename in all_files:

        skip = True
        for ending in ['sch.png', '.brd.png', '.top.brd.png', '.bot.brd.png']:
            if filename.lower().endswith(ending):
                skip = False

        root, ext = os.path.splitext(filename)
        if not skip:
            dest=args.queue.copy(projectname, version, filename)
            tag = root
            if filename.endswith("sch.png"):
                tag = 'Schematic'
            if filename.endswith(".brd.png"):
                tag = 'Board'
            if filename.endswith(".top.brd.png"):
                tag = 'Top Silk'
            if filename.endswith(".bot.brd.png"):
                tag = 'Bot Silk'
            s = "{sep}  - image_path: {dest}\n    title: {tag}\n"
            #s = "{sep}  - image_path: {dir}{project}/{version}/{filename}\n    title: {tag}\n"
            s = s.format(sep=sep, dest=dest,
                                  dir=args.conf.JEKYLL_URL_PUBLISH_DIR_EAGLE,
                                  project=projectname,
                                  version=version,
                                  filename=filename,
                                  tag=tag)
            output.write(s)
            # print("DEST= {}, IMAGE: {}".format(dest, s))
            sep = ""
    sep = 'artifacts:\n'
    for filename in sorted_nicely(all_files):
        for ending in ['.dpv', '.eagle.tar', '.eagle.zip', '.gerbers.tar', '.gerbers.zip', '.parts.csv']:
            if filename.endswith(ending):
                if project_state in ['broken', 'replaced']:
                    pass # continue
                root, ext = os.path.splitext(filename)

                pretext = 'download'
                tag = root
                posttext = ''
                if ext.lower() == '.dpv':
                    posttext = 'CHMT Component and feeder definitions'
                elif filename.endswith(".parts.csv"):
                    posttext = 'Parts List (spreadsheet data)'
                elif ext.lower() == '.docx':
                    posttext = 'Project Documentation'
                    tag = filename
                elif root.lower().endswith('.eagle'):
                    posttext = 'Eagle CAD files'
                    tag = filename
                elif root.lower().endswith('.gerbers'):
                    posttext = 'Gerber Fabrication files'
                    tag = filename
                else:
                    tag = filename
                # myroot = filename.replace(ending,"",1)
                # versionedfilename = "{root}-{version}{ext}".format(root=myroot, version=version, ext=ending)
                # print("Versioned filename = {}".format(versionedfilename))

                dest=args.queue.copy(projectname, version, filename)

                # s = "{sep}  - path: {dir}{project}/{version}/{filename}\n"
                s = "{sep}  - path: {dest}\n"
                s = s + "    tag: {tag}\n    type: {pretext}\n    post: {posttext}\n"
                s = s.format(sep=sep, dest=dest,
                                      dir=args.conf.JEKYLL_URL_PUBLISH_DIR_EAGLE,
                                      project=projectname,
                                      version=version,
                                      pretext=pretext,
                                      tag=tag,
                                      posttext=posttext,
                                      filename=filename,
                                      file=root)
                output.write(s)
                #print("artifact:  {}".format(s))
                sep = ""
    output.write('---\n')
    for filename in sorted_nicely(all_files):
        if filename.endswith('.bom.md'):
            if project_state in ['broken', 'replaced']:
                continue
            else:
                root, ext = os.path.splitext(filename)
                content_file = open(filename, 'r')
                if content_file:
                    output.write("\n")
                    output.write("## {}\n\n".format(root))
                    output.write(content_file.read())
                    content_file.close()


    if args.show:
        content = output.getvalue()
        print('# create {}'.format(outfilename))
        if args.verbose:
            print('====Contents====')
            print(content)
            print('================')
    else:
        output.close()


def processEagle(args):
    repo = Git("./")

    all_files = os.listdir(".")
    tag = repo.describe()
    #print("Tag={}".format(tag))

    processEagleParent(args, args.project, tag, all_files)
    processEagleChild(args, args.project, tag, all_files)


def main():
    conf = Configuration.Configuration("test")
    error = False
    
    parser = argparse.ArgumentParser(description='Generate project artifacts and copy them to the GitHub Jekyll docs repository.  Run this program in a project directory whenever you want to publish a (new or updated) design.')
    parser.add_argument("-F", "--Force", dest="force", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Force updates independent of timestamps.")
    parser.add_argument("-v", "--verbose", dest="verbose", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Print progress info.")
    parser.add_argument("-s", "--show", dest="show", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="Show what would be done, but don't change anything.")
    parser.add_argument("-n", "--name", dest="project", nargs=1, default=None,
                        help="Project Name (defaults to directory name)")
    parser.add_argument("-t", "--type", dest="projecttype", default=None, choices=['eagle', 'ino'])
    args = parser.parse_args()
    args.conf = conf
    
    autoconf = Location()
    autoconf.add("eagle",         conf.sourceDirIsEagle,           processEagle)
    autoconf.add("expresspcb",    conf.sourceDirIsExpressPCB,      processTODO)
    autoconf.add("lib",           conf.sourceDirIsArduinoLibrary,  processTODO)
    autoconf.add("controlpoint",  conf.sourceDirIsControlPoint,    processTODO)
    autoconf.add("ino",           conf.sourceDirIsArduino,         processArduino)
    autoconf.add("cad",           conf.sourceDirIsCAD,             processTODO)
    autoconf.add("script",        conf.sourceDirIsScript,          processTODO)
    autoconf.add("doc",           conf.sourceDirIsWikiDoc,         processTODO)

    cwd = os.getcwd()
    if args.projecttype is None:
        (args.srcdir, args.projecttype) = autoconf.find(cwd)
    else:
        (args.srcdir, x) = autoconf.find(cwd)
        if x != args.projecttype:
            print("Warning: Overriding directory structure default type of '{}' with '{}'".format(x, args.projecttype))

    if args.project is None:
        error = True
        print("Required --name argument not provided")
    else:
        args.project = args.project[0]

    if error:
        parser.print_help()
        sys.exit("incorrect usage")

    args.queue = CopyFile.CopyFile(conf, args)
    
    # /Users/plocher/Downloads/Dropbox/eagle/shields/RailroadShield
    # |------------ d e l e t e ------------|
    
    args.parentdir = os.path.dirname(cwd)
    args.subdir = cwd.replace(args.srcdir, "")
    if args.subdir[:1] == "/":
        args.subdir = args.subdir[1:]
    if (args.verbose):
        print("===============================")
        print("force    = {}".format(args.force))
        print("type     = {}".format(args.projecttype))
        print("name     = {}".format(args.project))
        print("verbose  = {}".format(args.verbose))
        print("show     = {}".format(args.show))
        print("srcdir   = {}".format(args.srcdir))   
        print("cwd        {}".format(cwd))
        print("parentdir  {}".format(args.parentdir))
        print("subdir     {}".format(args.subdir))
        print("===============================")
    
    # Create/update the project page
    content = autoconf.run(args)

    if not args.show:
        Path(conf.lastupload).touch()

if __name__ == "__main__":
    main()



