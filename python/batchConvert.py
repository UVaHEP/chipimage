#!/usr/bin/env python

# batch process tif data files in given directory
import getopt,commands,sys,glob,os
import argparse

# keep ROOT TApplication from grabbing -h flag
from ROOT import PyConfig
PyConfig.IgnoreCommandLineOptions = True
from ROOT import *


import tifftool

# global keep of all results
results={}  # dictionary
resList=[]  # list

# for finding background images, we assume the name of the same as the
# main image file, except that the voltage field is _0V_
def MakeFileLists(pathList, bkgSub=False):
    imgTmp=[]
    bkgTmp=[]
    imgFiles=[]
    bkgFiles=[]
    for path in pathList:
        if os.path.isdir(path):
            print "***",path
            bkgTmp.extend( glob.glob(path+'/*_0V*.ti*f') )
            imgTmp.extend( glob.glob(path+'/*.ti*f') )
        #if not ".tif" in path: continue
    print imgTmp
    if bkgSub:
        for tifname in imgTmp:
            if "_0V_" in tifname:
                continue
            else:  # note: finding Voltage will fail if a second "V_" is added 
                V=tifname.rsplit("V_",1)[0].rsplit("_",1)[1] 
                bkg=tifname.replace(V,"0")
                bkgmod=bkg.replace("_red_","_nofilter_")   # horrible
                bkgmod=bkgmod.replace("_green_","_nofilter_") # horrible
                bkgmod=bkgmod.replace("_blue_","_nofilter_")  # horrible
                if bkgmod in bkgTmp:
                    imgFiles.append(tifname)
                    bkgFiles.append(bkgmod)
                else: print "No background image found for",tifname
        return imgFiles,bkgFiles
    else:
        return imgTmp,bkgFiles  # keep all files in one array

    
def ProcessAll(tifFiles,bkgFiles=[]):        
    for i in range(len(tifFiles)):
        img=tifFiles[i]
        bkg=""
        print "Processing",img
        tfname = img.split(".tif")[0]+".root"
        pngname= img.split(".tif")[0]+".png"
        if len(bkgFiles)>0:
            bkg=bkgFiles[i]
            print "with background",bkg
            tfname=tfname.replace(".root","_Bsub.root")
            pngname=pngname.replace(".png","_Bsub.png")
        tf=TFile(tfname,"recreate")
        print "Saving output to",tfname
        imagedat=tifftool.tiff2TH2(img,bkg)
        imagedat["hImage"].Write()
        imagedat["iVals"].Write()
        imagedat["iValsL"].Write()
        print "Wrote",tf.GetName()
        tifftool.display(imagedat,pngname,False)
    return

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='I-V Curve Batch Processor')
    parser.add_argument('files', nargs='*')
    # not very useful. images close quickly
    parser.add_argument('-d', '--display', action='store_true', default=False,
                        help='display canvases during conversion')
    parser.add_argument('-b', '--bsub', action='store_true', default=False,
                        help='find and suptract background image')
    args = parser.parse_args()
    if not args.display: gROOT.SetBatch(True)  # batch mode, no canvas pop up
    pathList=args.files

    imgFiles,bkgFiles=MakeFileLists(pathList,args.bsub)

    #print imgFiles
    #print bkgFiles
    ProcessAll(imgFiles,bkgFiles)

