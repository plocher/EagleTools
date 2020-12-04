#!/bin/env python3

import os
import sys
import subprocess
import csv
import time
import sqlite3

import argparse

# Create tables
'''
projects:   id, projectname, date, version, status
partlist:   id, partname, partvalue, partpackage
inventory:  partvalue, partpackage, reelsize, componentheight, componentpitch, quantity, cost, owner

DATA INGEST

    walk projects in filesystem
        look for PROJECT-parts.csv or PROJECT_array-parts.csv (preferred if both found)
        determine version from git
        determine file mod time for brd (or _array.brd) file 
        LOOKUP project:  SELECT * from projects where projectname, version...
            if version not found or (version found, but mod time is newer than that cached in DB)
                open CSV file found above
                delete from partslist where id = projects.id (cuz we will replace the info)
                add to partslist items in CSV
                update projects.id with new timestamp/version
            else nothing to do

REPORTS

    per project BOM (componentvalue-componentpackage, projectname, quantity, cost/ea, total cost)
    global BOM (componentvalue-componentpackage, list of all projectnames that use component)
    Inventory update (append all components (value-package) to inventory if not found


'''

def createTables(args):
    conn = args.conn
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS Projects
                 (
                 projectid INTEGER NOT NULL PRIMARY KEY,
                 projectname text UNIQUE NOT NULL
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS BOMs
                 (
                 bomid INTEGER NOT NULL PRIMARY KEY,
                 projectid INTEGER UNIQUE NOT NULL,
                 version   text,
                 date      text UNIQUE
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS Components
                 (
                 componentid INTEGER NOT NULL PRIMARY KEY,
                 bomid      INTEGER NOT NULL,
                 partid     INTEGER,
                 name       text,
                 x          real,
                 y          real,
                 angle      real
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS Inventory
                 (
                 partid     INTEGER NOT NULL PRIMARY KEY,
                 type       text,
                 value      text, 
                 package    text,
                 component  text,
                 cost       real
                 )''')

    conn.commit()
    c.close()

def exportInventory(args, filename):
    conn = args.conn
    c = conn.cursor()
    c.execute('''SELECT package, value, type, component, partid, cost from Inventory ORDER BY package, value''')
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['#package', 'value', 'type', 'component', 'partid', 'cost'])
        for row in c.fetchall():
            writer.writerow(row)
    c.close()


def dumpTable(args, table):
    conn = args.conn
    c = conn.cursor()
    c.execute('''SELECT * from {}'''.format(table))
    print('===={}===='.format(table))
    for row in c.fetchall():
        print(row)
    c.close()
    print(input('--- PRESS RETURN --- \r'))

def dumpTables(args):
    dumpTable(args, 'Projects')
    dumpTable(args, 'BOMs')
    dumpTable(args, 'Components')
    dumpTable(args, 'Inventory')

'''
    walk projects in filesystem
    look for PROJECT-parts.csv or PROJECT_array-parts.csv (preferred if both found)
    determine version from git
    determine file mod time for brd (or _array.brd) file
'''

importedParts = {}

def loadInventory(args, filename):
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row[0][0] == '#':
                # OLD: Component, cost
                # Package, Value, Type, Component, PartID, Cost, Quantity, Stocked
                print (row)
                continue
            for x in range(len(row)):
                row[x] = row[x].strip().lower()
            if args.verbose:
                print("Add: ", end='')
                print(row)
            component = row[3].lower()
            cost      = row[5].lower()
            importedParts[component]=cost

def makePart(row):
    p = {}
    p['partid'] = row[0]
    p['type'] = row[1]
    p['value'] = row[2].lower()
    p['package'] = row[3].lower()
    p['component'] = row[4].lower()  # value-package
    p['cost'] = row[5]

    return p

def loadDB(args, projectname, filename, gitver, tstamp):
    # print('    Load DB {:<20} {} {} {}'.format(projectname, gitver, tstamp, filename))

    loadbom = False

    c = args.conn.cursor()
    c.execute('''SELECT projectid 
                 FROM Projects 
                 WHERE projectname = ?''', (projectname,))
    row = c.fetchone()
    if row is None:
        if args.verbose:
            print('Project: {} is not in Projects table.  Adding it...'.format(projectname))
        loadbom = True
        c.execute('''INSERT into Projects (projectname) 
                     VALUES (?)''', (projectname,))
        args.conn.commit()
        c.execute('''SELECT projectid 
                     FROM Projects 
                     WHERE projectname = ?''', (projectname,))
        row = c.fetchone()

    projectid = row[0]

    c.execute('''SELECT bomid, date, version 
                 FROM BOMs 
                 WHERE projectid = ? and version = ?''', (projectid, gitver))
    row = c.fetchone()
    if row is None:
        if args.verbose:
            print('BOM: {} is not in BOM table.  Adding it...'.format(projectname))
        loadbom = True
        c.execute('''INSERT into BOMs 
                    (projectid, version, date) VALUES (?,?,?)''', (projectid, gitver, tstamp))
        args.conn.commit()
        c.execute("SELECT bomid, date, version FROM BOMs where projectid = ? and version = ?", (projectid, gitver))
        row = c.fetchone()
    bomid    = row[0]
    dbtstamp = row[1]
    dbver    = row[2]

    # c.execute('''SELECT partid, type, value, package, component, cost
    #              FROM Inventory''')
    # rows = c.fetchall()
    # partlist = {}
    # for row in rows:
    #     p = makePart(row)
    #     partlist[p['component']] = p


    if loadbom:
        if args.verbose:
            print("Loading BOM entry\n\tproject:   {project}\n\tprojectid: {projectid}\n\tbomid:     {bomid}  version: {dbver} on date: {dbtstamp}".format(
               project=projectname,
               projectid=projectid,
               bomid=bomid,
               dbver=dbver, dbtstamp=dbtstamp,
               gitver=gitver, tstamp=tstamp))
    if (dbver != gitver):
        sys.exit('''
        ERROR - BOM entry with wrong version: should not happen!
            project:   {project}
            projectid: {projectid}
            bomid:     {bomid}
            DB:           version: {dbver} on date: {dbtstamp}
            Expected:     version: {gitver} on date: {tstamp}        
        '''.format(project=projectname,
                   projectid=projectid,
                   bomid=bomid,
                   dbver=dbver,   dbtstamp=dbtstamp,
                   gitver=gitver, tstamp=tstamp))
    if (dbtstamp != tstamp):
        if args.verbose:
            print("Updating BOM info for {}".format(projectname))
        loadbom = True

    if not loadbom:
        # Nothing to do
        return


    '''
    need to delete old BOM entries so we can load new ones
    as well as updating the timestamp on this new BOM set
    '''
    c.execute("BEGIN TRANSACTION")
    c.execute("DELETE from Components where bomid = ?", (bomid,))
    c.execute("UPDATE BOMs SET date = ? WHERE bomid = ?", (tstamp, bomid))
    c.execute('COMMIT')

    #args.conn.set_trace_callback(print)
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        try:
            for row in reader:
                if row[0][0] == '#':
                    #print (row)
                    continue

                for x in range(len(row)):
                    row[x] = row[x].strip().lower()
                #print("Add: ", end='')
                #print(row)
                name      = row[0]
                type      = row[1]
                value     = row[2]
                package   = row[3]
                component = row[4]
                x         = row[5]
                y         = row[6]
                a         = row[7]
                if not component in args.partlist:
                    # need to read in CSV file of existing inventory...
                    cost = 0
                    if component.lower() in importedParts:
                        cost = importedParts[component.lower()]
                    else:
                        print("Note: NEW Component, needs COST: {}".format(component))

                    c.execute('''INSERT into Inventory (type, value, package, component, cost)
                                 VALUES                (?,    ?,     ?,       ?,         ?)''',
                                                       (type, value, package, component,  cost))
                    c.execute('''SELECT partid, type, value, package, component, cost
                                 FROM Inventory
                                 WHERE component = ?''', (component,))
                    prow = c.fetchone()
                    p = makePart(prow)
                    args.partlist[component] = p

                partid = args.partlist[component]['partid']
                c.execute('''INSERT INTO Components (bomid, name, partid, x, y, angle)
                             VALUES                 (?,     ?,    ?,      ?, ?,  ? ) ''',
                             (bomid, name, partid, x, y, a))
                #print(input('--- PRESS RETURN --- \r'))


        except csv.Error as e:
            print('ERROR: csv reading file {}, line {}: {}'.format(filename, reader.line_num, e))
        args.conn.commit()
        #args.conn.set_trace_callback(None)
        c.close()

def process(args, dir, projectname):
    for pname in [ '{}_array'.format(projectname), '{}'.format(projectname) ]:
        partsfile = '{}.parts.csv'.format(pname)
        brdfile   = '{}.brd'.format(pname)
        pf = os.path.join(dir, partsfile)
        if os.path.exists(pf):
            olddir=os.getcwd()
            os.chdir(dir)
            ret = subprocess.run("make version", capture_output=True, shell=True, text=True)
            gitver = ret.stdout.rstrip()
            epochtime = os.path.getmtime(os.path.join(dir, brdfile))
            mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(epochtime))
            os.chdir(olddir)
            loadDB(args, projectname, pf, gitver, mtime)
            break
    else:
        print('    {} NOBODY HOME'.format(projectname))

def walk(args, directory):
    for f in os.listdir(directory):
        subdir = os.path.join(directory, f)
        if not os.path.isdir(subdir):
            continue
        if os.path.exists(os.path.join(subdir, '.git')):
            process(args, subdir, f)
        else:
            #print('    Looking at {}'.format(f))
            walk(args, subdir)

def main():
    parser = argparse.ArgumentParser(description="Maintain and query a database of components used in eagle projects")
    parser.add_argument("-c",  "--create",   action="store_true",
                                             help="Create a database file id needed")
    parser.add_argument("-i",  "--ingest",   action="store_true",
                                             help="Find and load in all project BOMs")
    parser.add_argument("-d",  "--debug",    action="store_true",
                                             help="generate debugging output")
    parser.add_argument("-v",  "--verbose",  type=int,  default=0, choices=[0, 1, 2],
                                             help="increase output verbosity")
    parser.add_argument("-db", "--database", nargs='?', type=str, default='/Users/jplocher/Dropbox/eagle/eagleBOM.db', const='./eagleBOM.db',
                                             help="database file to use")
    parser.add_argument("path",              nargs='*', type=list, default=['/Users/jplocher/Dropbox/eagle/onGitHub'],
                                             help="Path to Eagle Project dirs")

    args = parser.parse_args()

    if not os.path.exists(args.database):
        if args.create:
            args.conn = sqlite3.connect(args.database)
            createTables(args)
        else:
            sys.exit("ERROR: database file '{}' not found".format(args.database))
    else:
        args.conn = sqlite3.connect(args.database)

    if args.ingest:
        loadInventory(args, './ComponentCosts.csv')
        c = args.conn.cursor()
        c.execute('''SELECT partid, type, value, package, component, cost
                     FROM Inventory''')
        rows = c.fetchall()
        args.partlist = {}
        for row in rows:
            p = makePart(row)
            args.partlist[p['component']] = p
        c.close()

        eagleProjects = args.path
        for directory in eagleProjects:
            print('In {}'.format(directory))
            walk(args, directory)
        # Save (commit) the changes
        if args.conn.total_changes > 0:
            args.conn.commit()

    # Now the DB is up to date with all the project BOMs, generate the components list
    #dumpTables(args)

    c = args.conn.cursor()


    # Audit: Any parts without values?
    c.execute('''SELECT Projects.projectname, Inventory.package, Components.name
                 FROM Projects, Components, BOMS, Inventory
                 WHERE Projects.projectid = BOMs.projectid 
                 AND   BOMS.bomid = Components.bomid
                 AND   Components.partid = Inventory.partid
                 AND   Inventory.value = ''
                 ORDER BY projectname, package
                 ''')
    rows = c.fetchall()
    if len(rows):
        print("Audit: Components without values: {}".format(len(rows)))
        with open('novalues.csv', 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            for row in rows:
                csvwriter.writerow(row)
        print('Wrote novalues.csv')

    exportInventory(args, "inventory.csv")

    c.execute('''SELECT  Inventory.package, Inventory.component, Projects.projectname, count(*)
                 FROM    Projects, Components, BOMS, Inventory
                 WHERE   Projects.projectid = BOMs.projectid 
                 AND     BOMS.bomid = Components.bomid
                 AND     Components.partid = Inventory.partid
                 GROUP BY Projects.projectname, Inventory.component
                 ORDER BY Inventory.package
                 ''')
    rows = c.fetchall()
    if len(rows):
        print("Audit: Components used, by Project: {}".format(len(rows)))
        with open('usage.csv', 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['#Package', 'Component', 'Project', 'Usage'])
            for row in rows:
                csvwriter.writerow(row)
        print('Wrote usage.csv')

    c.close()
    args.conn.close()


if __name__ == "__main__":
    # execute only if run as a script
    main()
