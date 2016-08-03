# This is a demo reduce.py script

import sys
import os
import shutil

sys.path.append("/isis/NDXTEST/user/scripts/autoreduction") 
import reduce_vars as web_var

from mantid.simpleapi import *

import mantid

def main(input_file, output_dir):
    """ This is the (only) method required by the autoreduction interface. 
    
    input_file -- name of the input data file to reduce
    output_dir -- directory path to store file to
    
    To store files place use output_dir in combination with os.path.join() to
    to ensure that operating system dependent paths are handled correctly. For 
    example:
    
    fileToWriteTo = os.path.join(output_dir, "integrated.nxs")
    f = open(fileToWriteTo,"w")
    """
    
    # write out information set in mantid.user.properties to standard out
    # which should appear in *.out file in reduction_log subfolder
    configService = mantid.config
    print(configService.getInstrument())    

    # write out standard_vars to log
    for key, value in web_var.standard_vars.iteritems():
      logger.notice(str(key)+"="+str(value))

    # write out a dummy test file
    fileToWriteTo = os.path.join(output_dir, "dummyTestFile.txt")    
    f = open(fileToWriteTo,"w")
    f.write("Hello")
    f.close()    

    # copy input_file to output_dir    
    # shutil.copy(input_file, output_dir)
    
    # try to do some Mantid stuff
    # print("Load data, integrate and save to output_dir")     
    ws = Load(input_file)
    ws = Integration(ws)
    SaveNexus(ws, os.path.join(output_dir, "integrated.nxs"))

    # Define additional custom folder to copy results to
    # Note this folder needs to be visible by the autoreduction system
    #output_folder = '/isis/NDXWISH/Instrument/data/cycle_14_3/autoreduced/'    
    output_folder = ''
    return output_folder

if __name__ == "__main__":
    print("OK here we go")
    main('/isis/NDXGEM/Instrument/data/cycle_15_1/GEM00075513.nxs', '/home/reduce/reducedData')
    #main('\\isis\\NDXGEM\\Instrument\\data\\cycle_15_1\\GEM00075513.nxs', '/home/reduce/reducedData')
    #main('/home/reduce/tmp/test/testdata/testData.txt','/home/reduce/reducedData')

