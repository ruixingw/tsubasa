#!/home/rwang013/apps/python/bin/python3

 #################################################################
 # Tsubasa -- Get ready for Hessian Fitting Parameterization
 # Automated Optimization, Freq&Hessian, RESP Charge Calculation
 # First version by Ruixing at 2-Feb-2016
 #################################################################
from __future__ import print_function
from geomdef import *
from readfiles import *
import sys,os,time


pwd=sys.argv[0][:sys.argv[0].find('tsubasa.py')]
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
            g09rt=line[line.find('=''')+2:len(line)-2]

        if line.find('$g09a2rt')>=0:
            g09a2rt=line[line.find('=''')+2:len(line)-2]

        if line.find('$antechamber')>=0:
            antechamber=line[line.find('=''')+2:len(line)-2]

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
class GauFile(object):
    def __init__(self,name):
        self.name=name
        self.com=name+'.com'
        self.log=name+'.log'
        self.chk=name+'.chk'
        self.ac=name+'.ac'
    def rung09(self):
        print('Runing g09 with: '+g09rt+' '+self.com)
        os.system(g09rt+' '+self.com)
    def rung09a2(self):
        print('Runing g09a2 with: '+g09a2rt+' '+self.com)
        os.system(g09a2rt+' '+self.com)
    def isover(self):
        print('Waiting for g09...')
        while True:
            time.sleep(3)
            output=os.popen('tail -5 '+self.log)
            output=output.read()

            if output.find('Normal termination')>=0:
                print('..done\n\n')
                break
            if output.find('Error termination')>=0:
                print('Error termination in '+self.com)
                quit()
    def getresp(self):
        print('Runing antechamber: \n')
        os.system(antechamber+' -i '+self.log+' -fi gout -o '+self.ac+' -fo ac')


optname=GauFile('opt'+name)
freqname=GauFile('freq'+name)
respname=GauFile('resp'+name)

# Run Calculations
if startfrom<1:
    with open(name+'.gau','r') as initxyz:
        with open(optname.com,'w') as f:
            opthead='%chk=this.chk\n'+opthead
            f.write(opthead)
            f.write(initxyz.read())
            f.write(opttail)

    optname.rung09()
    optname.isover()
    os.system('cp this.chk '+optname.chk)
    if stopafter==1:
        print('User request stop after optimization')
        quit()
if startfrom<2:
    with open(freqname.com,'w') as f:
        freqhead='%chk=this.chk\n'+freqhead
        f.write(freqhead)
    freqname.rung09()
    freqname.isover()
    os.system('cp this.chk '+freqname.chk)
    if stopafter==2:
        print('User request stop after frequency')
        quit()
if startfrom<3:
    with open(respname.com,'w') as f:
        resphead='%chk=this.chk\n'+resphead
        f.write(resphead)
        f.write(resptail)
    respname.rung09a2()
    respname.isover()
    os.system('cp this.chk '+respname.chk)
    if stopafter==3:
        print('User request stop after resp')
        quit()
if startfrom<4:
    respname.getresp()
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
fchk=readfchk('this.fchk')
print('...done\n\nBuild mmxyz...')

for i in range(0,len(fchk.xyzlist),3):
    xyz.append(fchk.xyzlist[i:i+3])

for i in range(1,fchk.natoms+1):
     addatom(fchk.atomlist[i],xyz[i])   # Add Atoms
#Read ac file to get Charge&Atomtype and assign to atoms
if startfrom<5:
    ac=readac(respname.ac)
    for i in range(1,fchk.natoms+1):
        at[i].atomtype=ac.atomtype[i]
        at[i].charge=ac.charge[i]
if stopafter=='3':
    print('User request stop after readac')
    quit()

# Build MM File
mmxyz=fchk.charge+' '+fchk.spin+'\n'
def f2s(fl):
    return "{: .12f}".format(fl)

for i in range(1,fchk.natoms+1):
    mmxyz=mmxyz+at[i].elementname+'-'+at[i].atomtype+'-'+at[i].charge+'   '+f2s(at[i].x)+'   '+f2s(at[i].y)+'   '+f2s(at[i].z)+'\n'

mmxyz=mmxyz+'\n'

print('...done\n\nRead internal coordinates from optlog...')
# Read internal coordinates, add bond, angle, dihedral and define MM functions
with open(optname.log,'r') as f:
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
                    addbond(content[0],content[1])
                elif len(content)==3:
                    addangle(content[0],content[1],content[2])
                elif len(content)==4:
                    adddihd(content[0],content[1],content[2],content[3])
            break
print('...done\n\nBuild mmtail...')

for value in bonds.list.values():
    bondfunc(value)
for value in angles.list.values():
    anglefunc(value)
for value in dihedrals.list.values():
    dihdfunc(value)



def sortdihd(item):
    string=item.split()[1]+'-'+item.split()[2]
    return string
sorteddihd=sorted(dihdfunc.list.keys(),key=sortdihd)
def sortangle(item):
    string=item.split()[1]+'-'+item.split()[0]
    return string
sortedangle=sorted(anglefunc.list.keys(),key=sortangle)
def sortbond(item):
    string=item.split()[0]
    return string
sortedbond=sorted(bondfunc.list.keys(),key=sortbond)

#Build input file and MMtail(functions)
mmname=GauFile('mm'+name)
mmtail=''
input='natoms='+str(fchk.natoms)+'\nmmfile='+mmname.com+'\n'+'qmlog='+freqname.log+'\n'
input=input+'\n\nLink start\n'
# dihedral is assigned n=2 ,phase=180 and Npaths=1 temporarily

for key in sorteddihd:
    # key is dihdfunc, value is dihdobj
    mmtail=mmtail+'AmbTrs '+key+' 0 180 0 0 0.0 XXXXXX 0.0 0.0 1.0\n'
    # For each dihdfunc, look up for x in dihedral.list.obj to find out whose x.func match this key.
    # 'this' will be the dihedral links.
    this=filter(lambda x:x.func.link==key, dihedrals.list.values())
    this=list(set(this))
    for x in this:
        input+=str(x.a.atomid)+'-'+str(x.b.atomid)+'-'+str(x.c.atomid)+'-'+str(x.d.atomid)+'\n'
    input+='next  # '+key+'\n'

for key in sortedangle:
    this=filter(lambda x:x.func.link==key, angles.list.values())
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
    this=filter(lambda x:x.func.link==key, bonds.list.values())
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
    item.append(at[i].atomtype)
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

with open(mmname.com,'w') as f:
    f.write(mmhead)
    f.write(mmxyz)
    f.write(connectivity)
    f.write(mmtail)

print('...done\n\nEND')
os.system('mkdir tsubasa')
os.system('mv * tsubasa')
os.system('cp tsubasa/mm* .')
os.system('cp tsubasa/freq*.log .')
os.system('cp tsubasa/input.inp .')
