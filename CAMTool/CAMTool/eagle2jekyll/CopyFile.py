import os
import sys
import shutil

class CopyFile(object):
    def __init__(self, conf, args):
        self.conf  = conf
        self.args  = args
        self.pubdir = self.conf.JEKYLL_GITHUB_PUBLISH_DIR

        if conf.JEKYLL_GITHUB_PUBLISH_DIR and not os.path.isdir(conf.JEKYLL_GITHUB_PUBLISH_DIR):
            sys.exit("CopyFile Error: docdir does not exist - check configuration!\n")

    def copy(self, project, version, file):
        src = file
        if version:
            versionedfile = file.replace(".", "-{}.".format(version),1)
            dest = "{dir}{project}/{version}/{file}".format(dir=self.conf.JEKYLL_PUBLISH_VERSIONS_DIR,
                                                            project=project, version=version, file=versionedfile)
            local = "{dir}{project}/{version}/{file}".format(dir=self.conf.JEKYLL_URL_VERSIONS_DIR,
                                                            project=project, version=version, file=versionedfile)

        else:
            dest = "{dir}{project}/{file}".format(dir=self.conf.JEKYLL_PUBLISH_VERSIONS_DIR,
                                                  project=project, file=file)
            local = "{dir}{project}/{file}".format(dir=self.conf.JEKYLL_URL_VERSIONS_DIR,
                                                  project=project, file=file)

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

