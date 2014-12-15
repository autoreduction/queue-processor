import sys
import os
import shutil
from reduce_vars import *

def reduce(data, output_dir):
    shutil.copy(data, output_dir)

def main(*args, **kwargs):
   if not kwargs and sys.argv: #If called from command line
       if len(sys.argv) == 3 and '=' not in sys.argv:
           # with two simple inputs
           kwargs = { 'data' : sys.argv[1], 'output':sys.argv[2]}
       else:
           # With key value inputs
           kwargs = dict(x.split('=', 1) for x in sys.argv[1:])
   if not kwargs and 'data' not in kwargs and 'output' not in kwargs:
       raise ValueError("Data and Output paths must be supplied")
   
   # If additional storage location are required, return them as a list of accessible directory paths
   print kwargs
   additional_save_location = reduce(kwargs['data'], kwargs['output'])
   return additional_save_location


if __name__ == "__main__":
    main()
