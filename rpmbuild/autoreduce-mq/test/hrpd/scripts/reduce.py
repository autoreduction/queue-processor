import os
import sys
import shutil 
sys.path.append("/opt/Mantid/bin")
from mantid.simpleapi import *
import mantid

# first argument is full path (also called absolute path) 
# second argument is the output directory
eventFileAbs=sys.argv[1]
outputDir=sys.argv[2]

# get filename from full path
eventFile = os.path.split(eventFileAbs)[-1]

# get path
nexusDir = eventFileAbs.replace(eventFile, '')

#runNumber = eventFile.split('_')[1]
configService = mantid.config
dataSearchPath = configService.getDataSearchDirs()
dataSearchPath.append(nexusDir)
configService.setDataSearchDirs(";".join(dataSearchPath))

f = open(outputDir + "result_hrpd.txt",'w')
f.write("something")
f.close()

print "eventFileAbs = " + eventFileAbs
print "eventFile = " + eventFile
print "nexusDir = " + nexusDir
print "outputDir = " + outputDir
