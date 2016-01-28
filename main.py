import sys
import os
import time
string=sys.argv[1]
print 'Read input geometry from '+string+'\n'
name=string.split('.')[0]
string=string.split('.')[1]
if string != 'xyz' and string !='com':
    print 'Input geometry must be .xyz or .com'
    quit()

opthead=''
opttail=''
freqhead=''
resphead=''
resptail=''
mmhead=''
with open('config.cfg','r') as config:
    ifwrite=0
    for line in config.readlines():
        #Read commands
        if line.find('$g09boon')>=0:
            g09rt=line[line.find('=''')+2:len(line)-2]
        if line.find('$g09a2boon')>=0:
            g09a2rt=line[line.find('=''')+2:len(line)-2]
        if line.find('$antechamber')>=0:
            antechamber=line[line.find('=''')+2:len(line)-2]
        if line.find('$clean')>=0:
            clean=line[line.find('=''')+2:len(line)-2]

        #Read opthead
        if line.find('--opthead--')>=0:
            ifwrite=0
        if ifwrite==1:
            opthead=opthead+line
        if line.find('++opthead++')>=0:
            ifwrite=1

        #Read opttail
        if line.find('--opttail--')>=0:
            ifwrite=0
        if ifwrite==2:
            opttail=opttail+line
        if line.find('++opttail++')>=0:
            ifwrite=2

        #Read freqhead
        if line.find('--freqhead--')>=0:
            ifwrite=0
        if ifwrite==3:
            freqhead=freqhead+line
        if line.find('++freqhead++')>=0:
            ifwrite=3

        #Read resphead
        if line.find('--resphead--')>=0:
            ifwrite=0
        if ifwrite==4:
            resphead=resphead+line
        if line.find('++resphead++')>=0:
            ifwrite=4

        #Read resptail
        if line.find('--resptail--')>=0:
            ifwrite=0
        if ifwrite==5:
            resptail=resptail+line
        if line.find('++resptail++')>=0:
            ifwrite=5

        #Read mmhead
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
        print g09rt+' '+self.com()
        os.system(g09rt+' '+self.com())
    def rung09a2(self):
        print g09a2rt+' '+self.com()
        os.system(g09a2rt+' '+self.com())
    def isover(self):
        while True:
            time.sleep(3)
            output=os.popen('tail -5 '+self.log())
            output=output.read()
            print output
            if output.find('Normal termination')>=0:
                break
            if output.find('Error termination')>=0:
                print 'Error termination in '+self.com()
                quit()
    def getresp(self):
        os.system(antechamber+' -i '+self.log()+' -fi gout -o '+self.ac()+' -fo ac -c resp')

optname=GauFile('opt'+name)
freqname=GauFile('freq'+name)
respname=GauFile('resp'+name)

# Run Optimization
with open(sys.argv[1],'r') as initxyz:
    with open(optname.com(),'w') as optfile:
        optfile.write(opthead)
        optfile.write(initxyz.read())
        optfile.write(opttail)

optname.rung09()
optname.isover()

with open(freqname.com(),'w') as freqfile:
    freqfile.write(freqhead)
freqname.rung09()
freqname.isover()

with open(respname.com(),'w') as respfile:
    respfile.write(resphead)
    respfile.write(resptail)
respname.rung09a2()
respname.isover()
respname.getresp()


print clean
os.system(clean)
