"""
    Copy a file from the source location to the correct jekyll publishing location
    return the "url" name of the copied file

"""
__version__ = "0.1"


import os
import sys
import shutil

class CopyFile(object):
    def __init__(self, conf, args):
        self.conf  = conf
        self.args  = args
        if args.projecttype == "eagle":
            self.pubdir = self.conf.JEKYLL_GITHUB_PUBLISH_DIR_EAGLE
            self.copydir = self.conf.JEKYLL_LOCAL_PUBLISH_DIR_EAGLE
            self.urldir  = self.conf.JEKYLL_URL_PUBLISH_DIR_EAGLE
        elif args.projecttype == "ino":
            self.pubdir = self.conf.JEKYLL_GITHUB_PUBLISH_DIR_ARDUINO
            self.copydir = self.conf.JEKYLL_LOCAL_PUBLISH_DIR_ARDUINO
            self.urldir  = self.conf.JEKYLL_URL_PUBLISH_DIR_ARDUINO
        else:
            sys.exit("CopyFile Error: args.projecttype {} is not implemented!\n".format(args.projecttype))


        if self.pubdir and not os.path.isdir(self.pubdir):
            sys.exit("CopyFile Error: implied docdir {} does not exist - check configuration!\n".format(self.pubdir))

    def copy(self, project, version, file):
        src = file
        if version:
            versionedfile = file.replace(".", "-{}.".format(version),1)
            dest = "{dir}{project}/{version}/{file}".format(dir=self.copydir,
                                                            project=project,
                                                            version=version,
                                                            file=versionedfile)
            local = "{dir}{project}/{version}/{file}".format(dir=self.urldir,
                                                             project=project,
                                                             version=version,
                                                             file=versionedfile)

        else:
            dest = "{dir}{project}/{file}".format(dir=self.copydir,
                                                  project=project,
                                                  file=file)
            local = "{dir}{project}/{file}".format(dir=self.urldir,
                                                   project=project,
                                                   file=file)

        if self.pubdir:
            dest=os.path.join(self.pubdir, dest)

        if self.args.force:
            trigger = True
        elif not os.path.isfile(self.conf.lastupload):
            trigger = True
        elif not os.path.isfile(dest):
            trigger = True
        else:
            trigger = os.path.getmtime(src) > os.path.getmtime(self.conf.lastupload)


        if self.args.show:
            print("# +cp {src} {dest}".format(src=src, dest=dest))
        elif trigger:
            # check if any destination dirs need to be created
            d = dest
            d = os.path.dirname(d)
            if not os.path.isdir(d):
                if self.args.verbose:
                    print("+mkdir -p {dir}".format(dir=d))
                os.makedirs(d)
            if self.args.verbose:
                print("+cp {src} {dest}".format(src=src, dest=dest))
            shutil.copy2(src, dest)
        else:
            if self.args.verbose:
                print("# SKIP {src} => {dest}".format(src=src, dest=dest))
        return local

