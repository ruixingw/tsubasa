#!/usr/bin/env python3
 #################################################################
 # Tsubasa -- Get ready for Hessian Fitting Parameterization
 # Automated Optimization, Freq&Hessian, RESP Charge Calculation
 # First version by Ruixing at 2-Feb-2016
 #################################################################
from __future__ import print_function
import rxcclib.molecules as rxmol
import rxcclib.chemfiles as rxccfile
import sys,os,time,io,argparse,logging,pdb,shutil

################Parse input
parser=argparse.ArgumentParser()
parser.add_argument('-i',dest='inputgeom',default=False,help='Inputfile including molecular specs and connectivity')
parser.add_argument('-c',dest='configfile',default=False,help='Tsubasa config file.')
parser.add_argument('--readvdw',dest='externalvdwfile',default=False,help='If provided, read external vdW parameters from file',nargs=1)
args=parser.parse_args()
inputgeom=args.inputgeom
cfgfile=args.configfile
externalvdw=args.externalvdwfile
if externalvdw:
    externalvdw=externalvdw[0]
##############
############## copy config file to current path if no argument is specified
pwd=os.path.split(os.path.realpath(__file__))[0]
if inputgeom==False and cfgfile==False and externalvdw==False:
    gauname=False
    cfgname=False
    vdwname=False
    for filename in os.listdir():
        if filename.find('.gau')>=0:
            gauname=filename[0:filename.find('.gau')]
        if filename.find('.cfg')>=0:
            cfgname=filename[0:filename.find('.cfg')]
        if filename.find('vdw')>=0:
            externalvdw=filename
    if gauname!=False and cfgname!=False and cfgname!=gauname:
        logging.critical('Inconsistent name of inputgeom and config file. ')
        raise Exception
    elif gauname!=False and cfgname==False:
        shutil.copyfile(os.path.join(pwd,'config.cfg'),os.path.join(os.getcwd(),gauname+'.cfg'))
        logging.warning('Config file not found and it is copied to current directory. Program will now quit.')
        quit()
    elif gauname!=False and cfgname!=False and cfgname==gauname:
        inputgeom=gauname
        cfgfile=cfgname
    else:
        logging.critical('No inputgeom file found.')
        raise Exception
###########################


#### Logging module setting. Print INFO on screen and DEBUG INFO in file###########
logging.basicConfig(filename=inputgeom+'.tsubasa',level=logging.DEBUG,filemode='w')
console=logging.StreamHandler()
console.setLevel(logging.INFO)
formatter=logging.Formatter('%(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)
###################################################################################


quit()
if len(sys.argv)==1:
    os.system('cp '+pwd+'config.cfg .')
    quit()
string=sys.argv[1]
startfrom=0
stopafter=0
if string.find('.')>=0:
    name=string.split('.')[0]
    string=string.split('.')[1]
else:
    name=string
print('Read config from '+name+'.cfg\n')
if not os.path.isfile(name+'.cfg'):
    print(name+'.cfg does not exist! ')
    quit()
vdwfile=''

for x in sys.argv:
    if x.find('--startfrom')>=0:
        string=x.split(':')[1]
        if string=='freq':
            startfrom=1
            print('Restart from Frequency calculation')
        elif string=='resp':
            startfrom=2
            print('Restart from RESP calculation')
        elif string=='antechamber':
            startfrom=3
            print('Restart from antechamber')
        elif string=='readac':
            startfrom=4
            print('Restart from readac')

    if x.find('--stopafter')>=0:
        string=x.split(':')[1]
        if string=='opt':
            stopafter=1
            print('Will stop after optimization')
        elif string=='freq':
            stopafter=2
            print('Will stop after frequency')
        elif string=='resp':
            stopafter=3
            print('Will stop after resp')
        elif string=='antechamber':
            stopafter=4
            print('Will stop after antechamber')
        elif string=='readac':
            stopafter=5
            print('Will stop after readac')

    if x.find('--read-vdw-from')>=0:
        vdwfile=x.split(':')[1]
        print('External vdW parameter file provided:',vdwfile)


opthead=''
opttail=''
freqhead=''
resphead=''
resptail=''
mmhead=''
ifwrite=0
# Read configs
with open(name+'.cfg','r') as config:

    for line in config.readlines():
       # Read commands
        if line.find('$g09rt')>=0:
            rxccfile.gauCOM.g09rt=line[line.find('=''')+2:len(line)-2]

        if line.find('$g09a2rt')>=0:
            rxccfile.gauCOM.g09a2rt=line[line.find('=''')+2:len(line)-2]

        if line.find('$antechamber')>=0:
            rxccfile.amberAC.antechamber=line[line.find('=''')+2:len(line)-2]

        if line.find('$clean')>=0:
            clean=line[line.find('=''')+2:len(line)-2]

       # Read opthead
        if line.find('--opthead--')>=0:
            ifwrite=0

        if ifwrite==1:
            opthead=opthead+line
        if line.find('++opthead++')>=0:
            ifwrite=1


       # Read opttail
        if line.find('--opttail--')>=0:
            ifwrite=0
        if ifwrite==2:
            opttail=opttail+line
        if line.find('++opttail++')>=0:
            ifwrite=2

       # Read freqhead
        if line.find('--freqhead--')>=0:
            ifwrite=0
        if ifwrite==3:
            freqhead=freqhead+line
        if line.find('++freqhead++')>=0:
            ifwrite=3

       # Read resphead
        if line.find('--resphead--')>=0:
            ifwrite=0
        if ifwrite==4:
            resphead=resphead+line
        if line.find('++resphead++')>=0:
            ifwrite=4

       # Read resptail
        if line.find('--resptail--')>=0:
            ifwrite=0
        if ifwrite==5:
            resptail=resptail+line
        if line.find('++resptail++')>=0:
            ifwrite=5

       # Read mmhead
        if line.find('--mmhead--')>=0:
            ifwrite=0
        if ifwrite==6:
            mmhead=mmhead+line
        if line.find('++mmhead++')>=0:
            ifwrite=6

optname=rxccfile.File('opt'+name)
freqname=rxccfile.File('freq'+name)
respname=rxccfile.File('resp'+name)

# Run Calculations
if startfrom<1:
    with open(name+'.gau','r') as initxyz:
        with open(optname.comname,'w') as f:
            opthead='%chk=this.chk\n'+opthead
            f.write(opthead)
            f.write(initxyz.read())
            f.write(opttail)

    optname.com.rung09()
    if not optname.com.isover():
        quit()
    os.system('cp this.chk '+optname.chkname)
    if stopafter==1:
        print('User request stop after optimization')
        quit()
if startfrom<2:
    with open(freqname.comname,'w') as f:
        freqhead='%chk=this.chk\n'+freqhead
        f.write(freqhead)
    freqname.com.rung09()
    if not freqname.com.isover():
        quit()
    os.system('cp this.chk '+freqname.chkname)
    if stopafter==2:
        print('User request stop after frequency')
        quit()
if startfrom<3:
    with open(respname.comname,'w') as f:
        resphead='%chk=this.chk\n'+resphead
        f.write(resphead)
        f.write(resptail)
    respname.com.rung09a2()
    if not respname.com.isover():
        quit()
    os.system('cp this.chk '+respname.chkname)
    if stopafter==3:
        print('User request stop after resp')
        quit()
if startfrom<4:
    respname.log.runantecham()
    if stopafter==4:
        print('User request stop after antechamber')
        quit()


print('Clean directory: ')
print(clean)
print('\n')

os.system(clean)

print('Format CHK file by formchk: ')
os.system('formchk this.chk this.fchk')

#Read fchk : coordinates, charge, spin, natoms
fchk=rxccfile.File('this')
fchk.fchk.read()
print('...done\n\nBuild mmxyz...')
thisgeom=rxmol.Molecule('this')
xyz=['']
thisgeom.readfromxyz(io.StringIO(fchk.fchk.xyz))

#Read ac file to get Charge&Atomtype and assign to atoms
if startfrom<5:
    respname.ac.read()
    thisgeom.readchargefromlist(respname.ac.atomchargelist)
    thisgeom.readtypefromlist(respname.ac.atomtypelist)
if stopafter==3:
    print('User request stop after readac')
    quit()

# Build MM rxccfile.File
mmxyz=str(fchk.totalcharge)+' '+str(fchk.multiplicity)+'\n'
def f2s(fl):
    return "{: .12f}".format(fl)

for i in range(1,fchk.natoms+1):
    mmxyz=mmxyz+thisgeom[i].atomsym+'-'+thisgeom[i].atomtype+'-'+thisgeom[i].atomcharge+'   '+join(thisgeom[i].coords)+'\n'

mmxyz=mmxyz+'\n'

print('...done\n\nRead internal coordinates from optlog...')
# Read internal coordinates, add bond, angle, dihedral and define MM functions
with open(optname.logname,'r') as f:
    while True:
        string=f.readline()
        if string.find('Initial Parameters')>=0:
            f.readline()
            f.readline()
            f.readline()
            f.readline()
            while True:
                string=f.readline()
                if string.find('-------')>=0:
                    break
                content=string[string.find('(')+1:string.find(')')]
                content=content.split(',')
                content=[int(x) for x in content]
                if len(content)==2:
                    thisgeom.addbond(content[0],content[1])
                elif len(content)==3:
                    thisgeom.addangle(content[0],content[1],content[2])
                elif len(content)==4:
                    thisgeom.adddihd(content[0],content[1],content[2],content[3])
            break
print('...done\n\nBuild mmtail...')

for value in thisgeom.bonds.values():
    thisgeom.addbondfunc(value)
for value in thisgeom.angles.values():
    thisgeom.addanglefunc(value)
for value in thisgeom.dihedrals.values():
    thisgeom.adddihdfunc(value)




sorteddihd=sorted(thisgeom.dihdfunc.keys(),key=lambda item: item.split()[1]+'-'+item.split()[2])
sortedangle=sorted(thisgeom.anglefunc.keys(),key=lambda item: item.split()[1]+'-'+item.split()[0])
sortedbond=sorted(thisgeom.bondfunc.keys(),key=lambda item: item.split()[0])

#Build input file and MMtail(functions)
mmname=rxccfile.File('mm'+name)
mmtail=''
input='natoms='+str(fchk.natoms)+'\nmmfile='+mmname.comname+'\n'+'qmfchk='+freqname.fchkname+'\n'+'qmlog='+freqname.logname+'\n'
input=input+'\n\nLink start\n'
# dihedral is assigned n=2 ,phase=180 and Npaths=1 temporarily

for key in sorteddihd:
    # key is sorted dihdfunc
    mmtail=mmtail+'AmbTrs '+key+' 0 180 0 0 0.0 XXXXXX 0.0 0.0 1.0\n'
    # For each key of dihdfunc.key, filter x in dihedral.list.values(obj) to find out whose x.func(obj) match this key
    # 'this' will be the dihd obj who satisfy the condition aforementioned
    this=filter(lambda x:x.func.link==key, thisgeom.dihedrals.values())
    this=list(set(this))
    for x in this:
        input+=str(x.a.atomid)+'-'+str(x.b.atomid)+'-'+str(x.c.atomid)+'-'+str(x.d.atomid)+'\n'
    input+='next  # '+key+'\n'

for key in sortedangle:
    this=filter(lambda x:x.func.link==key, thisgeom.angles.values())
    this=list(set(this))
    total=0
    for x in this:
        total+=x.angle()
        input+=str(x.a.atomid)+'-'+str(x.b.atomid)+'-'+str(x.c.atomid)+'\n'
    input+='next  # '+key+'\n'
    total=total/len(this)
    total="{:.4f}".format(total)
    mmtail=mmtail+'HrmBnd1 '+key+' XXXXXX '+total+'\n'
for key in sortedbond:
    this=filter(lambda x:x.func.link==key, thisgeom.bonds.values())
    this=list(set(this))
    total=0
    for x in this:
        total+=x.length()
        input+=str(x.a.atomid)+'-'+str(x.b.atomid)+'\n'
    input+='next  # '+key+'\n'
    total=total/len(this)
    total="{:.5f}".format(total)
    mmtail=mmtail+'HrmStr1 '+key+' XXXXXX '+total+'\n'

#Add Nonbon function and vdW parameters
with open('input.inp','w') as f:
    f.write(input)
mmtail=mmtail+'Nonbon 3 1 0 0 0.0 0.0 0.5 0.0 0.0 -1.2\n'

radii={}
welldepth={}
#read all vdw in files
with open(pwd+'vdw.dat','r') as f:
    for string in f.readlines():
        item=string.split()
        radii.update({item[0].strip(' '):item[1].strip(' ')})
        welldepth.update({item[0].strip(' '):item[2].strip(' ')})
if vdwfile!='':
    print('Read user provided vdW parameters from',vdwfile)
    with open(vdwfile,'r') as f:
        for string in f.readlines():
            item=string.split()
            radii.update({item[0].strip(' '):item[1].strip(' ')})
            welldepth.update({item[0].strip(' '):item[2].strip(' ')})
item=[]
#find existing atomtypes
for i in range(1,fchk.natoms+1):
    item.append(thisgeom.atoms[i].atomtype)
item=list(set(item))
for i in range(0,len(item)):
    mmtail+='VDW '+item[i]+'  '+radii[item[i]]+'  '+welldepth[item[i]]+'\n'
mmtail=mmtail+'\n'
#write connectivity
connectivity=''
with open(name+'.gau','r') as f:
    ifread=0
    for line in f.readlines():
        if line=='\n':
            ifread=1
            continue
        if ifread==1:
            connectivity+=line
    connectivity+='\n'

with open(mmname.comname,'w') as f:
    f.write(mmhead)
    f.write(mmxyz)
    f.write(connectivity)
    f.write(mmtail)

print('...done\n\nEND')
os.system('mkdir tsubasa')
os.system('mv * tsubasa')
os.system('cp tsubasa/mm* .')
os.system('formchk tsubasa/'+freqname.chkname+' '+freqname.fchkname)
os.system('cp tsubasa/'+freqname.fchkname+' .')
os.system('cp tsubasa/'+freqname.logname+' .')
os.system('cp tsubasa/input.inp .')
