import os
import sys
from sys import platform
# For headless usage
import matplotlib
matplotlib.use('Agg')

# import mantid algorithms, numpy and matplotlib
from mantid.simpleapi import *
from mantid.api import AnalysisDataService as ADS
from matplotlib.colors import LogNorm
from matplotlib.ticker import LogLocator
import matplotlib.pyplot as plt
import numpy as np
import xml.etree.ElementTree as ET
import sans.command_interface.ISISCommandInterface as ici
import h5py as h5py
#print(dir(ici))
#print(help(ici.PhiRanges))

AUTOREDUCTION_DIR = r"/isis/NDXLARMOR/user/scripts/autoreduction"
sys.path.append(AUTOREDUCTION_DIR)

import reduce_vars as web_var

# set
inst='LARMOR'
cycle='20_3'
wavs=[1.0,3.0,5.0,7.0,9.0,11.0,13.0]
maskfile='USER_Jones_203A_Changer_r56068.txt'

def validate(input_file, output_dir):
    """
    Autoreduction validate Function
    -------------------------------
    Function to ensure that the files we want to use in reduction exist.
    Please add any files/directories to the required_files/dirs lists.
    """
    print("Running validation")
    required_files = [input_file]
    required_dirs = [output_dir]
    for file_path in required_files:
        if not os.path.isfile(file_path):
            raise RuntimeError("Unable to find file: {}".format(file_path))
    for dir in required_dirs:
        if not os.path.isdir(dir):
            raise RuntimeError("Unable to find directory: {}".format(dir))
    print("Validation successful")

# Main funcion that gets called by the reduction
def main(input_file, output_dir):
    #validate(input_file, output_dir)

    standard_params = web_var.standard_vars
    advanced_params = web_var.advanced_vars
    config['defaultsave.directory'] = output_dir

    # Check if the data set is marked as a SANS run
    # in the title by opening the nexus file directly
    # if the run title doesn't finish with _SANS do nothing
    f=h5py.File(input_file,'r')
    dataset_names=list(f.keys())
    main_data_set=dataset_names[0]
    main_group=f[main_data_set]
    title=main_group.get('title')[:][0].decode('UTF-8')
    f.close()
    runtype=title.split('_')[-1]
    NoneType=type(None)
    
    if runtype == 'SANS':
        SampleSANS=int(input_file[-12:-4])
        # ToDo: Put into function
        if standard_params['SampleTRANS'] != 'None' and type(standard_params['SampleTRANS']) != NoneType :
            SampleTRANS=int(standard_params['SampleTRANS'])
        else:
            SampleTRANS = None

        if standard_params['CanSANS'] != 'None' and type(standard_params['CanSANS']) != NoneType :
            CanSANS=int(standard_params['CanSANS'])
        else:
            CanSANS = None

        if standard_params['CanTRANS'] != 'None' and type(standard_params['CanTRANS']) != NoneType :
            CanTRANS=int(standard_params['CanTRANS'])
        else:
            CanTRANS = None

        if standard_params['EmptyBeamTRANS'] != 'None' and type(standard_params['EmptyBeamTRANS']) != NoneType :
            EmptyBeamTRANS=int(standard_params['EmptyBeamTRANS'])
        else:
            EmptyBeamTRANS = None

        if standard_params['RBNumber'] != 'None' and type(standard_params['RBNumber']) != NoneType :
            RBNumber=int(standard_params['RBNumber'])
        else:
            RBNumber = None

        userfile=standard_params['UserFile']

        # update the values of the various reduction runs from the journal
        # if possible. If the values are set by the web interface or the user
        # file then the value in the journal will be ignored
        rblist=sortRBs()
        if RBNumber != None:
            currRB=getCurrentRB(rblist,RBNumber)
            [meas,trans]=parseMeasurements(rblist[currRB])
            for i in range(len(meas)):
                if SampleSANS == meas[i][0]:
                    if SampleTRANS == None:
                        if meas[i][4] != -1:
                            SampleTRANS=meas[i][4]
                    if CanSANS == None:
                        if meas[i][2] != -1:
                            CanSANS=meas[i][2]
                    if CanTRANS == None:
                        if meas[i][5] != -1:
                            CanTRANS=meas[i][5]

        # now do the reduction using whatever values we have available.
        reduceSANS(sampleSANS=SampleSANS,sampleTRANS=SampleTRANS,canSANS=CanSANS, \
        canTRANS=CanTRANS,EBTRANS=EmptyBeamTRANS,maskfile=userfile,inst=inst,cycle=cycle, \
        wavs=advanced_params['wl_ranges'],outputdir=output_dir)

        # print a diagnostic string to a file
        debug='sampleSANS='+str(SampleSANS)+'\nsampleTRANS='+str(SampleTRANS)+'\ncansSANS='+str(CanSANS)
        debug+='\ncanTRANS='+str(CanTRANS)+'\nEBTRANS='+str(EmptyBeamTRANS)
        debug+='\nuserfile='+userfile+'\ninstrument='+inst+'\ncycle='+cycle
        debug+='\nwl_range='+str(advanced_params['wl_ranges'])+'\noutputdir='+output_dir
        print(debug,file=open(os.path.join(output_dir,'debug.txt'),'w'))
    else:
        # print a diagnostic string to a file
        debug='This was a TRANS run so there is nothing to output'
        print(debug,file=open(os.path.join(output_dir,'debug.txt'),'w'))
        

#========================================================================================
# Now the functions that actually do the reduction and plotting
#========================================================================================

def setDataSearchPath():
    # a bit of fiddling to check if this is a windows or unix system for testing
    if platform == "linux" or platform == "linux2":
        #prefix="/archive"
        # prefix for autoreduction system
        prefix="/isis"

    else:
        prefix="//isis/inst$"
#    ConfigService.setDataSearchDirs( \
#    prefix+"/NDX"+inst+"/User/Users/Masks/;"+ \
#    prefix+"/NDX"+inst+"/Instrument/data/cycle_"+cycle+"/")
    # on the headless server running autoreduction
    ConfigService.setDataSearchDirs( \
    prefix+"/NDX"+inst+"/User/Users/Masks/;"+ \
    prefix+"/NDX"+inst+"/Instrument/data/cycle_20_2/"+ \
    prefix+"/NDX"+inst+"/Instrument/data/cycle_"+cycle+"/")
    # on IDAaaS if the user area isn't visible
    #ConfigService.setDataSearchDirs( \
    #"/mnt/ceph/auxiliary/sans/Larmor/Masks/;"+ \
    #prefix+"/NDX"+inst+"/Instrument/data/cycle_"+cycle+"/")

def plot2Ddata(wkspname,titlewarning='',outputdir='',fig=None,axes=None):
    # fix 5.1 bug with monitor info in 2d workspaces
    for i in range(mtd[wkspname].getNumberHistograms()):
        mtd[wkspname].getSpectrum(i).clearDetectorIDs()
    if fig == None:
        fig, axes = plt.subplots(figsize=[8.0, 7.0], num=wkspname, subplot_kw={'projection': 'mantid'})
    cfill = axes.imshow(ADS.retrieve(wkspname), aspect='auto', cmap='viridis', distribution=True, origin='lower')
    zvals=ADS.retrieve(wkspname).extractY()
    zmin=np.amin(np.ma.masked_where(zvals==0, zvals))
    zmax=np.amax(zvals)
    if zmin < 0:
        zmin=1.0e-4
    if zmax < 0:
        zmax=1.0e-2
    xmin=ADS.retrieve(wkspname).dataX(0)[0]
    try:
        cfill.set_norm(LogNorm(vmin=zmin/2.0, vmax=zmax*2.0))
        # If no ticks appear on the color bar remove the subs argument inside the LogLocator below
        cbar = fig.colorbar(cfill, ax=axes, pad=0.06)
    except:
        cbar = fig.colorbar(cfill, ax=axes, pad=0.06)
    cbar.set_label('Cross Section (cm$^{-1}$)')
    if len(titlewarning) != 0:
        axes.set_title(titlewarning)
    else:
        axes.set_title(wkspname)
    axes.set_xlabel('Q$_{x}$ ($\\AA^{-1}$)')
    axes.set_ylabel('Q$_{y}$ ($\\AA^{-1}$)')
    # axes for QXY plots are symmetric
    axes.set_xlim([xmin, -xmin])
    axes.set_ylim([xmin, -xmin])
    #fig.savefig(os.path.join(output_dir, "QXY_Plot.png"), dpi=None)
    #if os.path.exists(outputdir):
    #    print(outputdir)
    #    print(os.path.join(outputdir,'2D_diagnostics.png'))
    #    fig.savefig(os.path.join(outputdir,'2D_diagnostics.png'),format='png')
    #fig.show()

#plot2Ddata('51040_rear_2D_0.9_13.5')

def plot1Dsectors(datalist,titlewarning='',fig=None,axes=None):
    title=datalist[0].split('_')[0]
    if fig == None:
        fig, axes = plt.subplots(num=title+'-sector', subplot_kw={'projection': 'mantid'})
    for i in datalist:
        axes.errorbar(ADS.retrieve(i), capsize=3.0, capthick=0.5, elinewidth=0.5, label=i, linewidth=0.5, specNum=1)
    if len(titlewarning) != 0:
        axes.set_title(titlewarning)
    else:
        axes.set_title(title+' Sector Overlap')
    axes.set_xlabel('q ($\AA^{-1}$)')
    axes.set_ylabel('1/cm')
    # Set the x axis to force a redraw
    axes.set_xlim([0.001, 1.0])
    axes.set_xscale('log')
    axes.set_yscale('log')
    axes.legend().draggable()
    #fig.savefig(os.path.join(output_dir, "Transmissions.png"), dpi=None)
    # comment this out when running headless
    #if fig == None:
    #    fig.show()

def plotTransmissions(datalist,titlewarning='',fig=None,axes=None):
    if len(datalist) > 0:
        title=datalist[0].split('_')[0]
        if fig == None:
            fig, axes = plt.subplots(num=title+'transmission', subplot_kw={'projection': 'mantid'})
        for i in datalist:
            axes.errorbar(ADS.retrieve(i), capsize=3.0, capthick=0.5, elinewidth=0.5, label=i, linewidth=0.5, wkspIndex=0)
    else:
        # create an empty plot with a title.
        if fig == None:
            fig, axes = plt.subplots(num=title+'transmission', subplot_kw={'projection': 'mantid'})        
        axes.errorbar([0,1],[0,0],[0,0])

    if len(titlewarning) != 0:
        axes.set_title(titlewarning)
    else:
        axes.set_title(title+' Transmissions')
    axes.set_xlabel('Wavelength ($\AA$)')
    axes.set_ylabel('Transmission')
    # Set the x axis to force a redraw
    axes.set_xlim([0.0, 14.0])
    axes.set_ylim([0.0, 1.2])
    axes.legend().draggable()
    #fig.savefig(os.path.join(output_dir, "Isotropic_Check_Plot.png"), dpi=None)
    # comment this out when running headless
    #if fig == None:
    #    fig.show()

def plot1Ddata(datalist,titlewarning='',fig=None,axes1=None,axes2=None,axes3=None):
    title=datalist[0].split('_')[0]
    if fig == None:
        fig, axes1 = plt.subplots(num=title+'_1d', subplot_kw={'projection': 'mantid'})
    axes1.errorbar(ADS.retrieve(datalist[0]), capsize=3.0, capthick=0.5, elinewidth=0.5, label=datalist[0], linewidth=0.5, specNum=1)
    if len(titlewarning) != 0:
        axes1.set_title(titlewarning)
    else:
        axes1.set_title(title+' 1D Reduction')
    axes1.set_xlabel('q ($\AA^{-1}$)')
    axes1.set_ylabel('1/cm')
    # Set the x axis to force a redraw
    axes1.set_xlim([0.001, 1.0])
    axes1.set_xscale('log')
    axes1.set_yscale('log')
    axes1.legend().draggable()
    #fig.savefig(os.path.join(output_dir, "1D_SANS_Plot.png"), dpi=None)
    # comment this out when running headless
    #if fig == None:
    #    fig.show()

    title=datalist[0].split('_')[0]
    if fig == None:
        fig, axes2 = plt.subplots(num=title, subplot_kw={'projection': 'mantid'})
    for i in datalist:
        axes2.errorbar(ADS.retrieve(i), capsize=3.0, capthick=0.5, elinewidth=0.5, label=i, linewidth=0.5, specNum=1)
    axes2.set_title(title+' Wavelength Overlap')
    axes2.set_xlabel('q ($\AA^{-1}$)')
    axes2.set_ylabel('1/cm')
    # Set the x axis to force a redraw
    axes2.set_xlim([0.001, 1.0])
    axes2.set_xscale('log')
    axes2.set_yscale('log')
    axes2.legend().draggable()
    #fig.savefig(os.path.join(output_dir, "Wavelength_Overlap_Plot.png"), dpi=None)
    # comment this out when running headless
    #if fig == None:
    #    fig.show()

    if fig == None:
        fig, axes3 = plt.subplots(num=title+'_1d', subplot_kw={'projection': 'mantid'})
    axes3.errorbar(ADS.retrieve(datalist[0]), capsize=3.0, capthick=0.5, elinewidth=0.5, label=datalist[0], linewidth=0.5, specNum=1)
    if len(titlewarning) != 0:
        axes3.set_title(titlewarning)
    else:
        axes3.set_title(title+' 1D Reduction')
    axes3.set_xlabel('q ($\AA^{-1}$)')
    axes3.set_ylabel('1/cm')
    # Set the x axis to force a redraw
    axes3.set_xlim([0.001, 1.0])
    axes3.legend().draggable()


def checkInputs(sampleSANS,sampleTRANS=None,canSANS=None,canTRANS=None,EBTRANS=None,maskfile=None):
    pass


def setupReduction(sampleSANS,sampleTRANS=None,canSANS=None,canTRANS=None,EBTRANS=None,maskfile=None,inst=inst,cycle=cycle):
    # Helper to setup the reduction so that it can be reset for the sector plots easily.
    # set the search path folders needed.
    setDataSearchPath()
    # initial 1d reduction
    ici.Clean()
    ici.UseCompatibilityMode()
    if inst == "LARMOR":
        ici.LARMOR()
    else:
        ici.LARMOR()

    ici.Set1D()

    if platform == "linux" or platform == "linux2":
        prefix="/archive"
    else:
        prefix="//isis/inst$"

    if len(maskfile)>0:
        #ici.MaskFile("/mnt/ceph/auxiliary/sans/Larmor/Masks/"+maskfile)
        ici.MaskFile(prefix+"/NDX"+inst+"/User/Users/Masks/"+maskfile)
    else:
        print('No Mask File Defined')
        return
    # assign the sample SANS run
    ici.AssignSample(prefix+"/NDX"+inst+"/Instrument/data/cycle_"+cycle+"/"+inst+"{:08d}.nxs".format(sampleSANS))

    titleoption=0
    # if a can has been specified assign it
    if canSANS is not None:
        ici.AssignCan(prefix+"/NDX"+inst+"/Instrument/data/cycle_"+cycle+"/"+inst+"{:08d}.nxs".format(canSANS))
        titleoption+=1

    # if a sample TRANS has been specified check that the empty beam has too and assign
    if sampleTRANS is not None and EBTRANS is not None:
        TRsam=prefix+"/NDX"+inst+"/Instrument/data/cycle_"+cycle+"/"+inst+"{:08d}.nxs".format(sampleTRANS)
        TREB=prefix+"/NDX"+inst+"/Instrument/data/cycle_"+cycle+"/"+inst+"{:08d}.nxs".format(EBTRANS)
        print(TRsam)
        print(TREB)
        ici.TransmissionSample(TRsam, TREB)
        titleoption+=1

    # if a can TRANS has been specified check that the empty beam has too and assign
    if canTRANS is not None and EBTRANS is not None:
        TRcan=prefix+"/NDX"+inst+"/Instrument/data/cycle_"+cycle+"/"+inst+"{:08d}.nxs".format(canTRANS)
        TREB=prefix+"/NDX"+inst+"/Instrument/data/cycle_"+cycle+"/"+inst+"{:08d}.nxs".format(EBTRANS)
        print(TRcan)
        print(TREB)
        ici.TransmissionCan(TRcan, TREB)
        titleoption+=1

    if titleoption == 0:
        titlewarning=''
    elif titleoption == 1:
        titlewarning=''
    elif titleoption == 2:
        titlewarning=''
    elif titleoption == 3:
        titlewarning=''

    return titlewarning

def reduceSANS(sampleSANS,sampleTRANS=None,canSANS=None,canTRANS=None,EBTRANS=None,maskfile=None,inst=inst,cycle=cycle,wavs=wavs,outputdir=''):
    # This is the function that runs everything using the sans instrument command interface
    # by default the reduction will just reduce the sample sans with no transmission.
    setupReduction(sampleSANS,sampleTRANS=sampleTRANS,canSANS=canSANS,canTRANS=canTRANS,EBTRANS=EBTRANS,maskfile=maskfile,inst=inst,cycle=cycle)

    wkspnames=[]
    # Perform the full reduction listed in the userfile
    wksp1d=ici.WavRangeReduction(None, None, ici.DefaultTrans)
    SaveNXcanSAS(wksp1d,os.path.join(outputdir,wksp1d+'_autoreduced.h5'))
    SaveRKH(wksp1d,os.path.join(outputdir,wksp1d+'_autoreduced.dat'))
    wkspnames.append(wksp1d)

    # the order of 2d then everything else is importand for the multiplot to work
    # perform the full 2d reduction in the user file
    ici.Set2D()
    #ici.WavRangeReduction(None, None, ici.DefaultTrans)
    wksp2d=ici.WavRangeReduction(None, None,ici.DefaultTrans)
    #SaveNexus(mtd["{}rear_2D_0.1_12.0".format(run)],join(base_dir,"{}_2D.nxs".format(run)))
    SaveNXcanSAS(wksp2d,os.path.join(outputdir,wksp2d+'_autoreduced.h5'))
    
    # Set up the figure for the 6 plots combined
    fig, axes = plt.subplots(2,3,figsize=[12.0, 8.0],num='Multiplot', subplot_kw={'projection': 'mantid'})
    # change the fontsize for the legends
    plt.rcParams['legend.fontsize']='x-small'
    # plot the 2d data seperately
    plot2Ddata(wksp2d,outputdir=outputdir,fig=fig,axes=axes[0,2])

    # check that the transmission workspaces exist and plot.
    transwksps=[]
    if mtd.doesExist(wksp1d.replace("rear_1D","trans_Sample")):
        transwksps.append(wksp1d.replace("rear_1D","trans_Sample"))
    if mtd.doesExist(wksp1d.replace("rear_1D","trans_Can")):
        transwksps.append(wksp1d.replace("rear_1D","trans_Can"))
    if mtd.doesExist(wksp1d.replace("rear_1D","trans_Sample_unfitted")):
        transwksps.append(wksp1d.replace("rear_1D","trans_Sample_unfitted"))
    if mtd.doesExist(wksp1d.replace("rear_1D","trans_Can_unfitted")):
        transwksps.append(wksp1d.replace("rear_1D","trans_Can_unfitted"))
    if len(transwksps) > 0:
        plotTransmissions(transwksps,fig=fig,axes=axes[0,0])
    else:
        plotTransmissions(transwksps,'No Transmission Data Found',fig=fig,axes=axes[0,0])



    # Now perform the overlap reduction with different wavelength ranges
    ici.Set1D()
    for i in range(len(wavs)-1):
        wksp1d=ici.WavRangeReduction(wavs[i], wavs[i+1], False)
        wkspnames.append(wksp1d)
    #SaveNexus(mtd["{}rear_1D_0.9_12.5".format(run)],join(base_dir,"{}_1D.nxs".format(run)))

    plot1Ddata(wkspnames,fig=fig,axes1=axes[1,2],axes2=axes[1,0],axes3=axes[0,1])

    # reset everything for the sector reduction
    wkspnames=[]
    setupReduction(sampleSANS,sampleTRANS=sampleTRANS,canSANS=canSANS,canTRANS=canTRANS,EBTRANS=EBTRANS,maskfile=maskfile,inst=inst,cycle=cycle)
    # perform reduction of 4 sectors to check for anisotropy
    ici.SetPhiLimit(0.0,180.0,use_mirror=False)
    wksp1d=ici.WavRangeReduction(None, None, ici.DefaultTrans)
    RenameWorkspace(wksp1d,wksp1d+'_top')
    wkspnames.append(wksp1d+'_top')
    ici.SetPhiLimit(180.0,360.0,use_mirror=False)
    wksp1d=ici.WavRangeReduction(None, None, ici.DefaultTrans)
    RenameWorkspace(wksp1d,wksp1d+'_bottom')
    wkspnames.append(wksp1d+'_bottom')
    ici.SetPhiLimit(90.0,270.0,use_mirror=False)
    wksp1d=ici.WavRangeReduction(None, None, ici.DefaultTrans)
    RenameWorkspace(wksp1d,wksp1d+'_left')
    wkspnames.append(wksp1d+'_left')
    ici.SetPhiLimit(-90.0,90.0,use_mirror=False)
    wksp1d=ici.WavRangeReduction(None, None, ici.DefaultTrans)
    RenameWorkspace(wksp1d,wksp1d+'_right')
    wkspnames.append(wksp1d+'_right')
    plot1Dsectors(wkspnames,fig=fig,axes=axes[1,1])

    fig.tight_layout()#pad=0.4, w_pad=0.5, h_pad=1.0)

    if os.path.exists(outputdir):
        print(outputdir)
        print(os.path.join(outputdir,inst+'{:08d}.png'.format(sampleSANS)))
        fig.savefig(os.path.join(outputdir,inst+'{:08d}.png'.format(sampleSANS)))
    #fig.show()
    #DeleteWorkspace("{}_sans_nxs".format(sampleSANS))
    #DeleteWorkspace("{}_sans_nxs_monitors".format(sampleSANS))


def getjournal(inst,cycle):
    url = 'http://data.isis.rl.ac.uk/journals/ndx'+inst.lower()+'/journal_'+cycle+'.xml'
    print(url)
    cmd='wget -O ~/temp.xml -c --read-timeout=5 --tries=0 '+url
    os.system('rm ~/temp.xml')
    os.system(cmd)

def getXMLInfo(inst=inst,cycle=cycle):
    if platform == "linux" or platform == "linux2":
        xmlfile="/archive/NDX"+inst+"/instrument/logs/journal/journal_"+cycle+".xml"
        if not os.path.exists(xmlfile):
            getjournal(inst,cycle)
            xmlfile=os.path.expanduser("~/temp.xml")
            #print(xmlfile)
    else:
        xmlfile="//isis/inst$/NDX"+inst+"/instrument/logs/journal/journal_"+cycle+".xml"

    tree = ET.parse(xmlfile)
    root = tree.getroot()
    i=0
    rnums = []
    rbnums = []
    titles = []
    for child in root:
        rnum = int(child.attrib['name'][-8:])
        rnums.append(rnum)
        rbnums.append(int(root[i][5].text))
        titles.append(root[i][0].text)
        i+=1
    return [rnums,rbnums,titles]

def parseTitle(runtitle):
    # this will need to be extended to accomodate other bits later
    bits=runtitle.split('_')
    runtype=bits[-1]
    title=titles[10][:-(len(runtype))-1]
    return [runtype,title]

def parseSANSTRANS(runtitle):
    us=list(find_all(runtitle,'_'))
    # if there are no _s in the title then we can't do anything so 
    # return as a trans so nothing happens
    if len(us) == 0:
        sanstrans=0
        return sanstrans
    st=runtitle[us[-1]+1:]
    sanstrans=-1
    if runtitle[us[-1]+1:] == 'SANS':
        sanstrans=1
        # now check if this is actually a TRANS_SANS run
        if len(us) > 1:
            if runtitle[us[-2]+1:us[-1]] == 'TRANS':
                sanstrans=2
    if runtitle[us[-1]+1:]== 'TRANS':
        sanstrans=0
    return sanstrans

def sortRBs():
    # Sort the journal list into rbnumberd lists
    rnums,rbnums,titles=getXMLInfo()
    rblist=[]
    firstrb=-1
    for i in range(len(rnums)):
        if rbnums[i] != firstrb or i == len(rnums)-1:
            if firstrb != -1:
                rblist.append([runs,rbs,rtitles])
            runs=[]
            rbs=[]
            rtitles=[]
            firstrb=rbnums[i]
        runs.append(int(rnums[i]))
        rbs.append(rbnums[i])
        rtitles.append(titles[i])
    return rblist

def findEB(rblist,rnum):
    # find the nearest empty beam run before the run of interest in the current RB
    ebnum=0
    for i in range(len(rblist[0])):
        #if rblist[0][i] < rnum:
        pass

def find_all(a_str, sub):
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1: return
        yield start
        start += len(sub) # use start += 1 to find overlapping matches

def gettitles(runtitle):
    lb=list(find_all(runtitle,'{'))
    rb=list(find_all(runtitle,'}'))
    if len(lb) == 1 and len(rb) == 1:
        samp=runtitle[lb[0]+1:rb[0]]
        can=''
    elif len(lb) == 2 and len(rb) == 2:
        samp=runtitle[lb[0]+1:rb[0]]
        can=runtitle[lb[1]+1:rb[1]]
    else:
        samp=runtitle
        can=''
    return [samp,can]

def parseMeasurements(rblist):
    meas=[]
    trans=[]
    # parse the list looking for samples, cans and transmissions
    for i in range(len(rblist[0])):
        # check if we have a SANS run or not, if so create a measurement
        st=parseSANSTRANS(rblist[2][i])
        if  st == 1:
            [samp,can]=gettitles(rblist[2][i])
            if len(can) == 0:
                meas.append([rblist[0][i],samp,-1,'',-1,-1])
            else:
                meas.append([rblist[0][i],samp,-1,can,-1,-1])
        elif st == 2:
            [samp,can]=gettitles(rblist[2][i])
            if len(can) == 0:
                meas.append([rblist[0][i],samp,-1,'',-1,-1])
            else:
                meas.append([rblist[0][i],samp,-1,can,-1,-1])

        else:
            [samp,can]=gettitles(rblist[2][i])
            trans.append([rblist[0][i],samp])
    # now look for the matching transmission runs
    for i in range(len(meas)):
        for j in range(len(trans)):
            if meas[i][1]==trans[j][1]:
                meas[i][4]=trans[j][0]
    # now look for can runs
    for i in range(len(meas)):
        for j in range(len(meas)):
            if meas[i][3]==meas[j][1] and len(meas[i][1])>0:
                meas[i][2]=meas[j][0]
    # finally look for can trans
    for i in range(len(meas)):
        for j in range(len(trans)):
            if meas[i][3]==trans[j][1] and len(meas[i][3])>0:
                meas[i][5]=trans[j][0]
    return [meas,trans]

def getCurrentRB(rblist,rbnumber):
    for i in range(len(rblist)):
        if rblist[i][1][0] == rbnumber:
            return i
            break
'''
rblist=sortRBs()
currRB=getCurrentRB(rblist,2010389)
currRB=getCurrentRB(rblist,2010523)
currRB=getCurrentRB(rblist,1910581)
[meas,trans]=parseMeasurements(rblist[currRB])
for i in range(len(meas)):
    print(meas[i])
'''
#reduceSANS(51040,51039,51038,51037,51037,maskfile=maskfile)
if __name__ == "__main__":
    #file='/archive/NDXLARMOR/Instrument/data/cycle_20_2/LARMOR00051565.nxs'
    #main(file,'/home/rd6564/AutoReduction/')
    main('','')


#print('test\ntest',file=open('/home/rd6564/AutoReduction/test.txt','w'))
