#!/home/rwang013/apps/python/bin/python3

 #################################################################
 # Tsubasa -- Get ready for Parameterization
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

print('Read config from '+string+'\n')
name=string.split('.')[0]
string=string.split('.')[1]
if string != 'cfg':
    print('Config must be .cfg')
    quit()


opthead=''
opttail=''
freqhead=''
resphead=''
resptail=''
mmhead=''
with open(name+'.cfg','r') as config:
    ifwrite=0
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
        print(g09rt+' '+self.com())
        os.system(g09rt+' '+self.com())
    def rung09a2(self):
        print(g09a2rt+' '+self.com())
        os.system(g09a2rt+' '+self.com())
    def isover(self):
        while True:
            time.sleep(3)
            output=os.popen('tail -5 '+self.log())
            output=output.read()
            os.system('clear')
            print(output)
            if output.find('Normal termination')>=0:
                break
            if output.find('Error termination')>=0:
                print('Error termination in '+self.com())
                quit()
    def getresp(self):
        os.system(antechamber+' -i '+self.log()+' -fi gout -o '+self.ac()+' -fo ac')


optname=GauFile('opt'+name)
freqname=GauFile('freq'+name)
respname=GauFile('resp'+name)

# Run Optimization
with open(name+'.xyz','r') as initxyz:
    with open(optname.com(),'w') as f:
        f.write(opthead)
        f.write(initxyz.read())
        f.write(opttail)

optname.rung09()
optname.isover()

with open(freqname.com(),'w') as f:
    f.write(freqhead)
freqname.rung09()
freqname.isover()

with open(respname.com(),'w') as f:
    f.write(resphead)
    f.write(resptail)
respname.rung09a2()
respname.isover()
respname.getresp()


print(clean)

os.system(clean)

os.system('formchk this.chk this.fchk')

xyzlist=[]
atomlist=['0']
print('proceeding to read fchk...')
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
print('fchk read successfully\nproceeding to build mmxyz')

for i in range(0,len(xyzlist),3):
    xyz.append(xyzlist[i:i+3])

for i in range(1,int(natoms)+1):
     addatom(atomlist[i],xyz[i])
with open(respname.ac(),'r') as f:
    string=f.readline()
    string=f.readline()
    for i in range(1,int(natoms)+1):
        string=f.readline()
        ac=string.split()
        at[i].atomtype=ac[len(ac)-1]
        at[i].charge=ac[len(ac)-2]
charge=charge.strip('\n')
spin=spin.strip('\n')

mmxyz=charge+' '+spin+'\n'
for i in range(1,int(natoms)+1):
    mmxyz=mmxyz+at[i].elementname+'-'+at[i].atomtype+'-'+at[i].charge+'   '+f2s(at[i].x)+'   '+f2s(at[i].y)+'   '+f2s(at[i].z)+'\n'

mmxyz=mmxyz+'\n'
print('mmxyz built successfully\nproceeding to read internal coordinates')
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
print('internal coordinates read\nproceeding to mmtail building')

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

for key,value in dihdfunc.df.items():
    mmtail=mmtail+'AmbTrs '+key+' 0 0 0 0 0.0 XXXXXX 0.0 0.0 1.0\n'
    this=filter(lambda x:x.df.link==key, dihedrals.dl.values())
    this=list(set(this))
    for x in this:
        input+=str(x.a.atomid)+'-'+str(x.d.atomid)+'\n'
    input+='next\n'
for key,value in anglefunc.af.items():
    this=filter(lambda x:x.af.link==key, angles.al.values())
    this=list(set(this))
    total=0
    for x in this:
        total+=x.angle()
        input+=str(x.a.atomid)+'-'+str(x.c.atomid)+'\n'
    input+='next\n'
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
    input+='next\n'
    total=total/len(this)
    total="{:.5f}".format(total)
    mmtail=mmtail+'HrmStr1 '+key+' XXXXXX '+total+'\n'


with open('input.inp','w') as f:
    f.write(input)
mmtail=mmtail+'Nonbon 3 1 0 0 0.0 0.0 0.5 0.0 0.0 -1.2\n'
radii={}
welldepth={}
with open(pwd+'vdw.dat','r') as f:
    while True:
        string=f.readline()
        if string.find('MOD4')>=0:
            string=f.readline()
            while string.find('END')<0:
                item=string.split()
                radii.update({item[0].strip(' '):item[1].strip(' ')})
                welldepth.update({item[0].strip(' '):item[2].strip(' ')})
                string=f.readline()
            break
item=[]
for i in range(1,int(natoms)+1):
    item.append(at[i].atomtype)
item=list(set(item))
for i in range(0,len(item)):
    mmtail+='VDW '+item[i]+'  '+radii[item[i]]+'  '+welldepth[item[i]]+'\n'
mmtail=mmtail+'\n'

connectivity=''
with open(name+'.xyz','r') as f:
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
