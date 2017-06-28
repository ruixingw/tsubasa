#!/usr/bin/env python3
#################################################################
# Tsubasa -- Get ready for Hessian Fitting Parameterization
# Automated Optimization, Freq&Hessian, RESP Charge Calculation
# First version by Ruixing at 2-Feb-2016
# Revision by Ruixing at 26-Jul-2016
#################################################################
import os
import sys
import yaml
import argparse
import logging
import shutil
import subprocess
import itertools


import rxcclib.Geometry.molecules as rxmol
import rxcclib.File.chemfiles as rxccfile


class TsubasaException(Exception):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return self.value

    __str__ = __repr__


class Bondfunc(object):
    def __init__(self, mole, bondobj):
        a = bondobj[1].atomtype
        b = bondobj[2].atomtype
        if a > b:
            a, b = b, a
        self.link = a + ' ' + b


class Anglefunc(object):
    def __init__(self, molecule, angleobj):
        a = angleobj[1].atomtype
        b = angleobj[2].atomtype
        c = angleobj[3].atomtype
        if a > c:
            a, c = c, a
        self.link = a + ' ' + b + ' ' + c


class Dihdfunc(object):
    def __init__(self, molecule, dihdobj):
        a = dihdobj[1].atomtype
        b = dihdobj[2].atomtype
        c = dihdobj[3].atomtype
        d = dihdobj[4].atomtype
        self.periodicity = 2
        self.phase = 0.0
        self.npaths = 1.0
        if b > c:
            a, d = d, a
            b, c = c, b
        elif b == c:
            if a > d:
                a, d = d, a
        self.link = a + ' ' + b + ' ' + c + ' ' + d


def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i',
                        dest='gaufile',
                        default=False,
                        help=('Inputfile including mo'
                              'lecular specs and connectivity'))
    parser.add_argument('-c',
                        dest='ymlfile',
                        default=False,
                        help='Tsubasa config file.')
    parser.add_argument('--readvdw',
                        dest='externalvdwfile',
                        default=False,
                        help=('If provided, read external vdW'
                              'parameters from file'), )
    parser.add_argument('--startfrom',
                        default='opt',
                        choices=['resp', 'antechamber', 'freq', 'buildMMfile'],
                        help=(
                            "Start from a certain step. Choices"
                            "=['resp','antechamber','freq','buildMMfile']"))
    parser.add_argument('--stopafter',
                        default='buildMMfile',
                        choices=['opt', 'resp', 'antechamber', 'freq'],
                        help=("Stop after a certain step."
                              " Choices=['opt','resp','antechamber','freq']"))
    parser.add_argument('--improper',
                        dest='improperlist',
                        default=False,
                        help=(
                            'Add improper functions,'
                            ' IMPROPERLIST should be a list like'
                            ' "h5 * c2 *,c3 * o *" '))
    args = parser.parse_args()
    return args


def loggingset(file=True):
    global myname
    # Logging module setting. Print INFO on screen and DEBUG INFO in file##
    if file is True:
        logging.basicConfig(filename=myname + '.tsubasa',
                            level=logging.DEBUG,
                            format=(
                                "%(asctime)s %(filename)s [line:%(lineno)d] "
                                "%(levelname)s %(message)s"),
                            datefmt='%d %b %H:%M:%S',
                            filemode='w', )
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(levelname)-8s %(message)s')
        console.setFormatter(formatter)
#        logging.getLogger('').addHandler(console)
    else:
        logging.basicConfig(level=logging.DEBUG,
                            format=('%(levelname)-8s %(message)s'))
    return None


def handleargs(args):
    global myname
    loggingset(file=False)
    if args.gaufile:
        logging.info("Provided gaufile: " + args.gaufile)
        if not os.path.isfile(args.gaufile):
            logging.critical(args.gaufile + " does not exist.")
            raise TsubasaException('File not found')
        loggingset(file=True)
    else:
        logging.info("Gaufile is not specified, will search for one.")
        for file in os.listdir():
            if os.path.splitext(file)[1] == '.gau':
                args.gaufile = file
                loggingset(file=True)
                logging.info('  ' + file + " is found as Gaufile.")
                break
        if not args.gaufile:
            logging.critical('Gaufile is not found.')
            raise TsubasaException('No Gaufile provided')
    myname = os.path.splitext(args.gaufile)[0]
    if args.ymlfile:
        logging.info("Provided config file: " + args.ymlfile)
        if not os.path.isfile(args.ymlfile):
            logging.critical(args.gaufile + " does not exist.")
            raise TsubasaException('File not found')
    else:
        args.ymlfile = os.path.splitext(args.gaufile)[0] + '.yml'
        logging.info("Config file is not provided, will search"
                     " for " + args.ymlfile)
        if os.path.isfile(args.ymlfile):
            logging.info('  ' + args.ymlfile + ' is found as config file.')
        else:
            logging.info('  ' + args.ymlfile + ' is not found. Copy a'
                         ' template and quit.')
            pwd = os.path.split(os.path.realpath(__file__))[0]
            shutil.copyfile(os.path.join(pwd, 'config.yml'), args.ymlfile)
            sys.exit()

    if args.externalvdwfile:
        logging.info("External vdW file is provided: " + args.externalvdwfile)
        if not os.path.isfile(args.externalvdwfile):
            logging.critical(args.externalvdwfile + " does not exist.")
            raise TsubasaException('File not found')

    ctrl = {}
    ctrl['opt'] = True
    ctrl['resp'] = True
    ctrl['antechamber'] = True
    ctrl['freq'] = True
    ctrl['buildMMfile'] = True
    if args.startfrom == 'resp':
        ctrl['opt'] = False
    elif args.startfrom == 'antechamber':
        ctrl['opt'] = False
        ctrl['resp'] = False
    elif args.startfrom == 'freq':
        ctrl['opt'] = False
        ctrl['resp'] = False
        ctrl['antechamber'] = False
    elif args.startfrom == 'buildMMfile':
        ctrl['opt'] = False
        ctrl['resp'] = False
        ctrl['antechamber'] = False
        ctrl['freq'] = False

    if args.stopafter == 'freq':
        ctrl['buildMMfile'] = None
    elif args.stopafter == 'antechamber':
        ctrl['freq'] = None
    elif args.stopafter == 'resp':
        ctrl['antechamber'] = None
    elif args.stopafter == 'opt':
        ctrl['resp'] = None
    return ctrl


def parseyml(args):
    global myname
    with open(args.ymlfile) as f:
        yml = f.read()
    blocks = yaml.load(yml)
    return blocks


def constructoptresp(args, blocks):
    global myname
    rxccfile.GauCOM.g09rt = blocks['g09rt']
    rxccfile.GauCOM.g09a2rt = blocks['g09a2rt']
    rxccfile.GauLOG.antecommand = blocks['antechamber']
    blocks['opthead'] += '\n'
    blocks['opttail'] += '\n'
    blocks['freqhead'] += '\n'
    blocks['resphead'] += '\n'
    blocks['resptail'] += '\n'
    blocks['mmhead'] += '\n'
    # build optfile and respfile
    with open(args.gaufile, 'r') as f:
        optfile = blocks['opthead'] + f.read() + blocks['opttail']
    respfile = blocks['resphead'] + blocks['resptail']
    respfile = '%chk=opt' + myname + '.chk\n' + respfile

    with open('opt' + myname + '.com', 'w') as f:
        f.write(optfile)
    with open('resp' + myname + '.com', 'w') as f:
        f.write(respfile)

    return


def runoptresp(ctrl):
    global myname
    tmp = ['opt', 'resp']
    files = {}
    for key in tmp:
        files[key] = rxccfile.File(key + myname)
        if ctrl[key] is True:
            if key == 'resp':
                files[key].com.rung09a2()
            else:
                files[key].com.rung09()
            try:
                files[key].com.isover()
                files[key].runformchk()
            except:
                logging.critical("Calculation failed for " + key)
                sys.exit()
        elif ctrl[key] is False:
            pass
        elif ctrl[key] is None:
            logging.info('User request stop before ' + key)
            sys.exit()
        else:
            raise TsubasaException('Unexcepted condition.')
    if ctrl['antechamber'] is True:
        logging.info('Run antechamber')
        files['resp'].log.runantecham()
    elif ctrl['antechamber'] is None:
        logging.info('User request stop before antechamber')
        sys.exit()
    elif ctrl['antechamber'] is False:
        pass
    else:
        raise TsubasaException('Unexcepted condition.')

    return files


def constructfreq(args, blocks, files):
    global myname
    #  read internal coordinates from optfile's connectivity
    optfile = files['opt']
    optfile.com.read()
    optmole = rxmol.Molecule('optmole')
    optmole.readfromxyz(optfile.com.xyz)
    optmole.readconnectivity(optfile.com.connectivity)

    # read types from respfile.mol2
    respfile = files['resp']
    respfile.mol2.read()
    optmole.readchargefromlist(respfile.mol2.atomchargelist)
    optmole.readtypefromlist(respfile.mol2.atomtypelist)

    # prepare freqtail (internal coordinates)
    freqtail = '* * K\n* * * K\n* * * * K\n'
    for key in optmole._bondlist.keys():
        freqtail += ' '.join(key.split('-')) + ' A\n'
    for key in optmole._anglelist.keys():
        freqtail += ' '.join(key.split('-')) + ' A\n'
    for key in optmole._dihdlist.keys():
        freqtail += ' '.join(key.split('-')) + ' A\n'
    if args.improperlist:
        # add Improper from improperlist
        # parse improperlist
        improperlist = args.improperlist
        improperlist = improperlist.split(',')
        improperlist = [x.split() for x in improperlist]

        # find improper
        for item in improperlist:
            for atom3 in optmole:
                if atom3.atomtype == item[2]:
                    permu = list(itertools.permutations(atom3.neighbor, 3))
                    success = []
                    for tu in permu:
                        a = tu[0].atomtype == item[0] or item[0] == '*'
                        b = tu[1].atomtype == item[1] or item[1] == '*'
                        c = tu[2].atomtype == item[3] or item[3] == '*'
                        if a and b and c:
                            success.append([tu[0].atomnum, tu[1].atomnum,
                                            atom3.atomnum, tu[2].atomnum])

                    success = sorted(success, key=lambda x: str(x[1]) + str(x[3]))
                    success = success[0]
                    optmole.addimproper(*success)

        # add improper internal coordinate
        for key in optmole.improperlist.keys():
            freqtail += ' '.join(key.split('-')) + ' A\n'

    blocks['freqfile'] = blocks['freqhead'] + freqtail + '\n'
    blocks['freqfile'] = '%chk=opt' + myname + '.chk\n' + blocks['freqfile']
    with open('freq' + myname + '.com', 'w') as f:
        f.write(blocks['freqfile'])

    pass


def runfreq(ctrl, files):
    files['freq'] = rxccfile.File('freq' + myname)

    if ctrl['freq'] is None:
        logging.info('User request stop before freq.')
        sys.exit()
    elif ctrl['freq'] is True:
        pass
    elif ctrl['freq'] is False:
        return files

    if ctrl['freq'] is True:
        files['freq'].com.rung09()
        try:
            files['freq'].com.isover()
            files['freq'].runformchk()
        except:
            logging.critical("Calculation failed for " + 'freq')
            sys.exit()
    elif ctrl['freq'] is False:
        pass
    elif ctrl['freq'] is None:
        logging.info('User request stop before ' + 'freq')
        sys.exit()
    else:
        raise TsubasaException('Unexcepted condition.')

    return files


def tsubasa(files):
    global myname
    # readfchk
    qmfile = files['freq']
    qmfile.runformchk()
    qmfile.fchk.read()
    respfile = files['resp']
    respfile.mol2.read()

    files['opt'].com.read()
    thisgeom = rxmol.Molecule('this')
    thisgeom.readfromxyz(qmfile.fchk.xyz)
    thisgeom.readconnectivity(files['opt'].com.connectivity)

    thisgeom.readchargefromlist(respfile.mol2.atomchargelist)
    thisgeom.readtypefromlist(respfile.mol2.atomtypelist)

    return thisgeom


def buildmmfile(thisgeom, files, args, mmhead):
    global myname
    qmfile = files['freq']
    externalvdwfile = args.externalvdwfile
    # Build MM input
    mmxyz = str(qmfile.totalcharge) + ' ' + str(qmfile.multiplicity) + '\n'

    def f2s(fl):
        return "{: .12f}".format(fl)

    for i in range(1, qmfile.natoms + 1):
        mmxyz = mmxyz + thisgeom[i].elementsym + '-' + thisgeom[
            i].atomtype + '-' + '{:.6f}'.format(thisgeom[
                i].atomcharge) + '   ' + '   '.join(
                    [f2s(x) for x in thisgeom[i].coords]) + '\n'

    mmxyz = mmxyz + '\n'

    thisgeom.dihdfunc = {}
    thisgeom.anglefunc = {}
    thisgeom.bondfunc = {}
    for bond in thisgeom.bondlist.values():
        thisfunc = Bondfunc(thisgeom, bond)
        thisgeom.bondfunc.update({thisfunc.link: bond})
        bond.func = thisfunc
    for angle in thisgeom.anglelist.values():
        thisfunc = Anglefunc(thisgeom, angle)
        thisgeom.anglefunc.update({thisfunc.link: angle})
        angle.func = thisfunc
    for dihd in thisgeom.dihdlist.values():
        thisfunc = Dihdfunc(thisgeom, dihd)
        thisgeom.dihdfunc.update({thisfunc.link: dihd})
        dihd.func = thisfunc


    # Read internal coordinates, add bond, angle, dihedral
    # and define MM functions
    sorteddihd = sorted(thisgeom.dihdfunc.keys(),
                        key=lambda x: x.split()[1] + ' ' + x.split()[2])
    sortedangle = sorted(thisgeom.anglefunc.keys(),
                         key=lambda x: x.split()[1] + ' ' + x.split()[0])
    sortedbond = sorted(thisgeom.bondfunc.keys(), key=lambda x: x.split()[0])

    # Build input file and MMtail(functions)
    mmfile = rxccfile.File('mm' + myname)
    mmtail = ''
    input = 'natoms=' + str(qmfile.natoms) + '\nmmfile=' + os.path.split(
        mmfile.comname)[1] + '\n' + 'qmfchk=' + os.path.split(qmfile.fchkname)[
            1] + '\n' + 'qmlog=' + os.path.split(qmfile.logname)[1] + '\n'
    input = input + '\n\nLink start\n'

    # dihedral is assigned n=2 ,phase=0 and Npaths=1 temporarily

    for key in sorteddihd:
        # key is sorted dihdfunc
        mmtail = (
            mmtail + 'AmbTrs ' + key + ' 0 0 0 0 0.0 XXXXXX 0.0 0.0 ')
        # For each key of dihdfunc.key, filter x in
        # dihedral.list.values(obj) to find
        # out whose x.func(obj) match this key
        # 'this' will be the dihd obj who satisfy the condition aforementioned
        this = filter(lambda x: x.func.link == key, thisgeom.dihdlist.values())
        this = list(set(this))
        for x in this:
            input += str(x[1].atomnum) + '-' + str(x[2].atomnum) + '-' + str(x[
                3].atomnum) + '-' + str(x[4].atomnum) + '\n'
        npaths = (len(x[2].neighbor)-1) * (len(x[3].neighbor)-1)
        mmtail += '{:.1f}'.format(npaths) + '\n'
        input += 'next  # ' + key + '\n'

    for key in sortedangle:
        this = filter(lambda x: x.func.link == key,
                      thisgeom.anglelist.values())
        this = list(set(this))
        total = 0
        for num, x in enumerate(this):
            total += x.anglevalue
            now = total / (num + 1)
            if abs(x.anglevalue - now) > 3 and total != 0:
                logging.warning(
                    'Angle ' + x.repr +
                    ' has very different angle value of  {:.4f}'.format(
                        x.anglevalue) + ' compared to ' + x.func.link +
                    ' {:.4f}'.format(now))
            input += str(x[1].atomnum) + '-' + str(x[2].atomnum) + '-' + str(x[
                3].atomnum) + '\n'
        input += 'next  # ' + key + '\n'
        total = total / len(this)
        total = "{:.4f}".format(total)
        mmtail = mmtail + 'HrmBnd1 ' + key + ' XXXXXX ' + total + '\n'
    for key in sortedbond:
        this = filter(lambda x: x.func.link == key, thisgeom.bondlist.values())
        this = list(set(this))
        total = 0
        for num, x in enumerate(this):
            total += x.length
            now = total / (num + 1)
            if abs(x.length - now) > 0.1 and total != 0:
                logging.warning('bond ' + x.repr +
                                ' has very different length of {:.4f}'.format(
                                    x.length) + ' compared to ' + x.func.link +
                                ' {:.5f}'.format(now))
            input += str(x[1].atomnum) + '-' + str(x[2].atomnum) + '\n'
        input += 'next  # ' + key + '\n'
        total = total / len(this)
        total = "{:.5f}".format(total)
        mmtail = mmtail + 'HrmStr1 ' + key + ' XXXXXX ' + total + '\n'

    # Add impropers
    if args.improperlist:
        improperlist = args.improperlist
        improperlist = improperlist.split(',')
        improperlist = [x.split() for x in improperlist]
        for item in improperlist:
            mmtail += 'ImpTrs  ' + ' '.join(item) + '  XXXXXX 180.0 2.0\n'

    # Add Nonbon function and vdW parameters
    with open('input.inp', 'w') as f:
        f.write(input)
    mmtail = mmtail + 'Nonbon 3 1 0 0 0.0 0.0 0.5 0.0 0.0 -1.2\n'

    radii = {}
    welldepth = {}
    # read all vdw in files
    with open(
            os.path.join(
            os.path.split(os.path.realpath(__file__))[0],
            'vdw.dat'), 'r'
    ) as f:
        for string in f:
            item = string.split()
            radii.update({item[0].strip(' '): item[1].strip(' ')})
            welldepth.update({item[0].strip(' '): item[2].strip(' ')})
    try:
        if externalvdwfile:
            logging.info('Read user provided vdW parameters from ' +
                         externalvdwfile)
            with open(externalvdwfile, 'r') as f:
                for string in f:
                    item = string.split()
                    radii.update({item[0].strip(' '): item[1].strip(' ')})
                    welldepth.update({item[0].strip(' '): item[2].strip(' ')})
    except:
        logging.error('Read user provided vdW file failed. Please check the format.')

    item = []

    # find existing atomtypes
    for atom in thisgeom:
        item.append(atom.atomtype)
    item = list(set(item))
    for i in range(0, len(item)):
        try:
            mmtail += 'VDW ' + item[i] + '  ' + radii[item[i]] + '  ' + welldepth[
                item[i]] + '\n'
        except KeyError:
            mmtail += 'VDW ' + item[i] + '  ' + 'RADII' + '  ' + 'WELLDEPTH' + '\n'
    mmtail = mmtail + '\n'

    # write mmfile
    with open(mmfile.comname, 'w') as f:
        f.write(mmhead)
        f.write(mmxyz)
        f.write(files['opt'].com.connectivity)
        f.write('\n')
        f.write(mmtail)

    logging.debug('...done\n\nEND')

    os.system('mkdir tsubasa')
    os.system('mv * tsubasa')
    os.system('cp tsubasa/mm* .')
    os.system('cp tsubasa/' + os.path.split(qmfile.fchkname)[1] + ' .')
    os.system('cp tsubasa/' + os.path.split(qmfile.fchkname)[1] + ' .')
    os.system('cp tsubasa/' + os.path.split(qmfile.logname)[1] + ' .')
    os.system('cp tsubasa/input.inp .')

    pass


def main():
    global myname
    myname = ''
    args = argparser()
    ctrl = handleargs(args)
    blocks = parseyml(args)
    constructoptresp(args, blocks)
    files = runoptresp(ctrl)
    constructfreq(args, blocks, files)
    files = runfreq(ctrl, files)
    thisgeom = tsubasa(files)

    buildmmfile(thisgeom, files, args, blocks['mmhead'])

    subprocess.run(blocks['clean'], shell=True)
    pass


if __name__ == '__main__':
    global myname
    main()
