#!/usr/bin/python

 #################################################################
 # Tsubasa -- Get ready for Hessian Fitting Parameterization
 # Automated Optimization, Freq&Hessian, RESP Charge Calculation
 # V0.1 Ruixing 2-Feb-2016
 #################################################################
from __future__ import print_function
from head import *
import sys,os,time


pwd=sys.argv[0][:sys.argv[0].find('tsubasa.py')]
if len(sys.argv)==1:
    os.system('cp '+pwd+'config.cfg .')
    quit()
string=sys.argv[1]
startfrom=0
stopafter=0
print('Read config from '+string+'\n')
name=string.split('.')[0]
string=string.split('.')[1]
if string != 'cfg':
    print('Config must be .cfg')
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
    def com(self):
        return self.name+'.com'
    def log(self):
        return self.name+'.log'
    def ac(self):
        return self.name+'.ac'
    def rung09(self):
        print('Runing g09 with: '+g09rt+' '+self.com())
        os.system(g09rt+' '+self.com())
    def rung09a2(self):
        print('Runing g09a2 with: '+g09a2rt+' '+self.com())
        os.system(g09a2rt+' '+self.com())
    def isover(self):
        print('Waiting for g09...')
        while True:
            time.sleep(3)
            output=os.popen('tail -5 '+self.log())
            output=output.read()

            if output.find('Normal termination')>=0:
                print('..done\n\n')
                break
            if output.find('Error termination')>=0:
                print('Error termination in '+self.com())
                quit()
    def getresp(self):
        print('Runing antechamber: \n')
        os.system(antechamber+' -i '+self.log()+' -fi gout -o '+self.ac()+' -fo ac')


optname=GauFile('opt'+name)
freqname=GauFile('freq'+name)
respname=GauFile('resp'+name)

# Run Calculations
if startfrom<1:
    with open(name+'.gau','r') as initxyz:
        with open(optname.com(),'w') as f:
            f.write(opthead)
            f.write(initxyz.read())
            f.write(opttail)

    optname.rung09()
    optname.isover()
    if stopafter==1:
        print('User request stop after optimization')
        quit()
if startfrom<2:
    with open(freqname.com(),'w') as f:
        f.write(freqhead)
    freqname.rung09()
    freqname.isover()
    if stopafter==2:
        print('User request stop after frequency')
        quit()
if startfrom<3:
    with open(respname.com(),'w') as f:
        f.write(resphead)
        f.write(resptail)
    respname.rung09a2()
    respname.isover()
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

print('Format CHK file with formchk: ')
os.system('formchk this.chk this.fchk\n\n')
# From fchk read Charge, Multiplicity, Coordinates
xyzlist=[]
atomlist=['0']
print('Read fchk...')
with open('this.fchk','r') as f:
    while True:
        string=f.readline()
        if string.find('Charge')>=0:
            charge=string.split('I')[1].strip(' ')
        if string.find('Multiplicity')>=0:
            spin=string.split('I')[1].strip(' ')
        if string.find('Atomic numbers')>=0:
            natoms=string.split('=')[1].strip(' ')
            while True:
                string=f.readline()
                if string.find('Nuclear charges')>=0:
                    break
                for x in string.split():
                    atomlist.append(x.strip(' '))

        if string.find('Current cartesian')>=0:
            while True:
                string=f.readline()
                if string.find('Force Field')>=0:
                    break
                for x in string.split():
                    xyzlist.append(x.strip(' '))
            break

xyzlist=[float(x) for x in xyzlist]
atomlist=[int(x) for x in atomlist]

print('...done\n\nBuild mmxyz...')

for i in range(0,len(xyzlist),3):
    xyz.append(xyzlist[i:i+3])

for i in range(1,int(natoms)+1):
     addatom(atomlist[i],xyz[i])   # Add Atoms
#Read ac file to get Charge&Atomtype
if startfrom<5:
    with open(respname.ac(),'r') as f:
        string=f.readline()
        string=f.readline()
        for i in range(1,int(natoms)+1):
            string=f.readline()
            ac=string.split()
            at[i].atomtype=ac[len(ac)-1]
            at[i].charge=ac[len(ac)-2]
if stopafter=='3':
    print('User request stop after readac')
    quit()
# Build MM Coordinates
charge=charge.strip('\n')
spin=spin.strip('\n')
mmxyz=charge+' '+spin+'\n'
for i in range(1,int(natoms)+1):
    mmxyz=mmxyz+at[i].elementname+'-'+at[i].atomtype+'-'+at[i].charge+'   '+f2s(at[i].x)+'   '+f2s(at[i].y)+'   '+f2s(at[i].z)+'\n'

mmxyz=mmxyz+'\n'
print('...done\n\nRead internal coordinates from optlog...')
# Read internal coordinates
with open(optname.log(),'r') as f:
    while True:
        string=f.readline()
        if string.find('Optimized Parameters')>=0:
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

for value in bonds.bl.values():
    bondfunc(value)
for value in angles.al.values():
    anglefunc(value)
for value in dihedrals.dl.values():
    dihdfunc(value)


mmname=GauFile('mm'+name)
mmtail=''
input='natoms='+natoms+'mmfile='+mmname.com()+'\n'+'qmlog='+freqname.log()+'\n'
input=input+'\n\nLink start\n'
# Build MM functions
for key,value in dihdfunc.df.items():
    mmtail=mmtail+'AmbTrs '+key+' 0 0 0 0 0.0 XXXXXX 0.0 0.0 1.0\n'
    this=filter(lambda x:x.df.link==key, dihedrals.dl.values())
    this=list(set(this))

    for x in this:
        input+=str(x.a.atomid)+'-'+str(x.b.atomid)+'-'+str(x.c.atomid)+'-'+str(x.d.atomid)+'\n'
    input+='next  # '+key+'\n'
for key,value in anglefunc.af.items():
    this=filter(lambda x:x.af.link==key, angles.al.values())
    this=list(set(this))
    total=0
    for x in this:
        total+=x.angle()
        input+=str(x.a.atomid)+'-'+str(x.b.atomid)+'-'+str(x.c.atomid)+'\n'
    input+='next  # '+key+'\n'
    total=total/len(this)
    total="{:.4f}".format(total)
    mmtail=mmtail+'HrmBnd1 '+key+' XXXXXX '+total+'\n'
for key,value in bondfunc.bf.items():
    this=filter(lambda x:x.bf.link==key, bonds.bl.values())
    this=list(set(this))
    total=0
    for x in this:
        total+=x.length()
        input+=str(x.a.atomid)+'-'+str(x.b.atomid)+'\n'
    input+='next  # '+key+'\n'
    total=total/len(this)
    total="{:.5f}".format(total)
    mmtail=mmtail+'HrmStr1 '+key+' XXXXXX '+total+'\n'


with open('input.inp','w') as f:
    f.write(input)
mmtail=mmtail+'Nonbon 3 1 0 0 0.0 0.0 0.5 0.0 0.0 -1.2\n'
radii={}
welldepth={}
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
for i in range(1,int(natoms)+1):
    item.append(at[i].atomtype)
item=list(set(item))
for i in range(0,len(item)):
    mmtail+='VDW '+item[i]+'  '+radii[item[i]]+'  '+welldepth[item[i]]+'\n'
mmtail=mmtail+'\n'

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

with open(mmname.com(),'w') as f:
    f.write(mmhead)
    f.write(mmxyz)
    f.write(connectivity)
    f.write(mmtail)

print('...done\n\nEND')
os.system('mkdir tsubasa')
os.system('mv * tsubasa')
os.system('mv tsubasa/mm* .')
os.system('mv tsubasa/freq*.log .')
os.system('mv tsubasa/input.inp .')
