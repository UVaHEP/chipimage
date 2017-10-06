#!/usr/bin/env python

# batch process tif data files in given directory

# keep ROOT TApplication from grabbing -h flag
from ROOT import PyConfig
PyConfig.IgnoreCommandLineOptions = True
from ROOT import *

import getopt,commands,sys,glob,os
import argparse
import tifftool

# global keep of all results
results={}  # dictionary
resList=[]  # list



def MakeFileLists(pathList):
    tiffFiles=[]
    for path in pathList:
        if os.path.isdir(path):
            print "***",path
            tiffFiles.extend( glob.glob(path+'/*.tif') )
            tiffFiles.extend( glob.glob(path+'/*.tiff') )
        if not ".tif" in path: continue
    return tiffFiles

def ProcessAll(tifFiles):        

    for img in tifFiles:
        print "Processing",img
        tfname = img.split(".tif")[0]+".root"
        pngname= img.split(".tif")[0]+".png"
        tf=TFile(tfname,"recreate")
        print "Saving output to",tfname
        imagedat=tifftool.tiff2TH2(img)
        imagedat["hImage"].Write()
        imagedat["iVals"].Write()
        imagedat["iValsL"].Write()
        print "Wrote",tf.GetName()
        tifftool.display(imagedat,pngname,False)
    return

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='I-V Curve Batch Processor')
    parser.add_argument('files', nargs='*')
    args = parser.parse_args()
       
    pathList=args.files

    tiffFiles=MakeFileLists(pathList)
    #print tiffFiles
    
    ProcessAll(tiffFiles)

