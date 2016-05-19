# Tsubasa


## Overview
### What is it?
*Tsubasa* is a program to prepare input files for Hessian Fitting parameterization.
### Why is it?
Hessian Fitting scheme requires QM optimized geometry, Hessian, RESP charge, and a MM input file. Preparing MM input file for Hessian Fitting is a very complicated work. The major difficulty is identifying MM functions. MM functions are all bond types, angle types and dihedral types. Manually identifying all MM functions without a miss is hard for large molecule. The equilibrium values of harmonic terms (bond stretching and angle bending) are averaged from many bond distances or angles, while this procedure is also complicated for human. *Tsubasa* program automatically do all calculations, identify MM functions and format every thing done into a MM input file, which is eventually used by Hessian Fitting programs.

## Installation

### Dependencies
Tsubasa requires the following packages.

- [Python3](https://www.python.org/) ([Anaconda](https://www.continuum.io/downloads) is strongly recommended)
- [numpy](http://www.numpy.org/) (Included in Anaconda)
- [cclib](https://cclib.github.io/) (simply install by ```pip install cclib```)
- [rxcclib](https://github.com/ruixingw/rxcclib) 

### Get Tsubasa
1. Clone this repository by ```git clone https://github.com/ruixingw/tsubasa.git```.
2. Add the ```tsubasa``` directory to your $PATH environment.

## Quick Start

An example of benzene (C<sub>6</sub>H<sub>6</sub>) is shown here.

1) Prepare Input file including geometry and connectivity.

The input file can be easily prepared by GaussView and deleting some lines. The format is as followed.

```
0 1
C     -0.196066032299      0.083954610270      0.000060359368
C      1.202825076336      0.083884471006      0.000506018868
C      1.902331654047      1.295325035437     -0.000047136416
C      1.202946707718      2.506835148041     -0.001045596240
C     -0.195944409385      2.506905316939     -0.001491091778
C     -0.895450997150      1.295464738220     -0.000938299116
H     -0.739751345816     -0.857625934164      0.000489987063
H      1.746416421211     -0.857750015636      0.001281451623
H      2.989606822804      1.295270625436      0.000299297106
H      1.746632277886      3.448415533193     -0.001475037473
H     -0.739536124154      3.448539598789     -0.002266379146
H     -1.982726171199      1.295519560979     -0.001284573853

1 2 1.5 6 1.5 7 1.0
2 3 1.5 8 1.0
3 4 1.5 9 1.0
4 5 1.5 10 1.0
5 6 1.5 11 1.0
6 12 1.0
7
8
9
10
11
12

```

Note that there is a blank line at the end. Save this file with a ".gau" extension, for example, "ben.gau".

2) Run "tsubasa.py". A config file will be copied to the current folder and named as "ben.cfg".

3) Modify the config file according to your own needs. For details, please see the manual. In this example, we only modify the "opttail" part to set the basis set.
```
++opttail++
C H 0
6-31+g*
****

--opttail--
```
4) Run "tsubasa.py" again. Program will now automatically perform Optimization, Frequency calculation, RESP calculation, and identify the internal coordinates and MM functions, and finally prepare MM input file. Files are saved in "tsubasa" folder.
```
   ruixingw@boonlay-ntu test $ ls
   freqben.fchk  freqben.log  input.inp  mmben.com  tsubasa/
   ruixingw@boonlay-ntu test $ cd tsubasa
   ben.cfg  ben.tsubasa  freqben.com   freqben.log  mmben.com   optben.com  respben.ac   respben.com
   ben.gau  freqben.chk  freqben.fchk  input.inp    optben.chk  optben.log  respben.chk  respben.log
```

The **mmben.com** and **freqben.fchk** is then used to perform Hessian Fitting job. **freqben.log** is used to evaluate the performance (L1 Norm of frequencies). **input.inp** includes internal coordinates information but is not used for now. 

The content of **mmben.com** is as follow.

```
%mem=12gb
#p amber=softonly geom=connectivity nosymm
iop(4/33=3,7/33=1)
freq=noraman

MM-name

0 1
C-ca--0.117738   -0.196066032299    0.083954610270    0.000060359368
C-ca--0.117738    1.202825076336    0.083884471006    0.000506018868
C-ca--0.117738    1.902331654047    1.295325035437   -0.000047136416
C-ca--0.117738    1.202946707718    2.506835148041   -0.001045596240
C-ca--0.117738   -0.195944409385    2.506905316939   -0.001491091778
C-ca--0.117738   -0.895450997150    1.295464738220   -0.000938299116
H-ha-0.117738   -0.739751345816   -0.857625934164    0.000489987063
H-ha-0.117738    1.746416421211   -0.857750015636    0.001281451623
H-ha-0.117738    2.989606822804    1.295270625436    0.000299297106
H-ha-0.117738    1.746632277886    3.448415533193   -0.001475037473
H-ha-0.117738   -0.739536124154    3.448539598789   -0.002266379146
H-ha-0.117738   -1.982726171199    1.295519560979   -0.001284573853

1 2 1.5 6 1.5 7 1.0
2 3 1.5 8 1.0
3 4 1.5 9 1.0
4 5 1.5 10 1.0
5 6 1.5 11 1.0
6 12 1.0
7
8
9
10
11
12

AmbTrs ca ca ca ca 0 180 0 0 0.0 XXXXXX 0.0 0.0 1.0
AmbTrs ha ca ca ca 0 180 0 0 0.0 XXXXXX 0.0 0.0 1.0
AmbTrs ha ca ca ha 0 180 0 0 0.0 XXXXXX 0.0 0.0 1.0
HrmBnd1 ca ca ha XXXXXX 120.0000
HrmBnd1 ca ca ca XXXXXX 120.0000
HrmStr1 ca ha XXXXXX 1.08728
HrmStr1 ca ca XXXXXX 1.39889
Nonbon 3 1 0 0 0.0 0.0 0.5 0.0 0.0 -1.2
VDW ca  1.9080  0.0860
VDW ha  1.4590  0.0150

```

5) The dihedrals are separately idenfied and they are assigned n=2, phase=180 degree and NPaths=1.0. One must manually edit dihedral MM functions according to his own need.
```
AmbTrs * ca ca * 0 180 0 0 0.0 XXXXXX 0.0 0.0 4.0
```

## Other options
For other options, please see the Tsubasa Reference Manual.

