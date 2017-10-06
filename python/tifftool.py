#!/usr/bin/python

from ROOT import *
from math import log
from math import exp
from PIL import Image
from PIL import ImageOps
from array import array
import os, sys
import argparse

    
# inputs
# imgFile: image data tiff
# title: title for histogram version of image 
# bkg: optional background histogram
# useLog: flag to take log of pixel data
# lowcut: use to suppress pixels.  if pixel<lowcut : pixel=0


def tiff2TH2(imgFile, title=None, bkg=None, useLog=False, lowcut=150):
    em1=exp(1)
    imagedat={}
    if title==None:
        title=os.path.basename(imgFile).split(".tif")[0]
    img = Image.open(imgFile)
    #ImageOps.equalize(img.convert('L')).show()
    #ImageOps.autocontrast(img.convert('L')).show()
    wid,height=img.size
    npix=wid*height
    print "Image size:",wid,height
    imgarray=img.getdata()
    maxpix=max(imgarray)
    print "max pixel value",maxpix
    if maxpix>=32768: print "Warning: Oveflow(s) of signed short"
    if bkg:
        imbkg=Image.open(bkg)
        bkgdat=imbkg.getdata()
    imagedat["hImage"]=TH2S("hImage",title,wid,-0.5,wid-0.5,height,-0.5,height-0.5)
    #imagedat["hImage"]=TH2C("hImage",title,wid,-0.5,wid-0.5,height,-0.5,height-0.5)
    imagedat["iVals"]=TH1I("hIntensity","Intensity Distribution",1056,-1024.5,32767.5)
    imagedat["iValsL"]=TH1I("hIntensityL","Intensity Distribution",1024,0,log(32767.5))
    for col in range(wid):
        for row in range(height):
            idx=col*wid+row
            val=imgarray[idx]
            imagedat["iVals"].Fill(min(val,32767))
            imagedat["iValsL"].Fill(log(max(val,1)))
            if bkg: val=max(val-bkgdat[idx],0)
            if useLog: val=log(max(imgarray[idx],em1))
            if val<lowcut: val=1
            imagedat["hImage"].SetBinContent(row,height-1-col,val)
            #ival=int(log(max(1,val))*23)
            #imagedat["hImage"].Fill(row,height-1-col,ival-128)

    # set min/max pixels on corners to fix the range for color thresholds
    imagedat["hImage"].SetBinContent(1,1,32767)
    imagedat["hImage"].SetBinContent(wid,height,1)
    imagedat["noise"]=imagedat["iVals"].GetBinCenter(imagedat["iVals"].GetMaximumBin())
    print "Estimated mean noise (counts)",imagedat["noise"]
    print "min, max pixel values", imagedat["hImage"].GetMinimum(), imagedat["hImage"].GetMaximum()
    return imagedat


# kill pixels if surrounding area contains fraction < thresh of pixel value
# might be useful for isolated, single pixel spikes
def killhotpix(hin,thresh=0.05):
    nx=hin[0].GetNbinsX()
    ny=hin[0].GetNbinsY()
    for col in range(nx):
        E=min(nx-1,col+1)
        W=max(0,col-1)
        for row in range(ny):
            val=hin[0].GetBinContent(col,row)
            # sum over (up to) 3x3 area around pixel
            N=min(ny-1,row+1)
            S=max(0,row-1)
            sum=0
            # loop over box coords. take (sum-val)/val = sum/val-1
            for ix in range(W,E+1):
                for iy in range (S,N+1):
                    sum=sum+hin[0].GetBinContent(ix,iy)
            if val>0 and (sum/val-1.0)<thresh:   # here is a spike
                hin[0].SetBinContent(row,col,0)

def setContours(imagedat):
    palette=array('i')
    noise=imagedat["noise"]
    # try setting levels based on noise
    # default # of contours is 20, so work with these for now
    # assume noise*20 < ~327678
    # note sure if these contours are doing anything....probably no
    #imagedat["hImage"].SetContourLevel(0,-2*noise)
    #for i in range(1,20):
    #    imagedat["hImage"].SetContourLevel(i,noise*i)
    gStyle.SetPalette(kGreyScale)
    

def display(imagedat,pngfile=None,wait=True):
    gStyle.SetOptStat(0)
    c2=TCanvas("c2","c2",200,50,850,850)
    c2.SetCanvasSize(800,800);
    c2.DrawFrame(0,0,20,20);
    c2.SetLogz()
    setContours(imagedat)
    imagedat["hImage"].Draw("col")
    if pngfile==None: pngfile=imagedat["hImage"].GetTitle()+".png"
    c2.SaveAs(pngfile)
    if wait:
        print 'Hit return to exit'
        sys.stdout.flush()
        raw_input('')

        
if __name__ == "__main__":
    if len(sys.argv)<2:
        print "No file name given"
        sys.exit()

    parser = argparse.ArgumentParser(description='16 bit Tiff conversion tool')
    parser.add_argument('files', nargs='*', help="Give file path(s) to conversion")

    parser.add_argument('-i', '--image', type=str, 
                        default=None, help="Input image file")
    
    parser.add_argument('-b', '--background', type=str, 
                        default=None, help="Background image file")

    parser.add_argument('-o', '--output', type=str, 
                        default=None, help="[Optional] output root file name")

    parser.add_argument('-d', '--display', default=None, help="Display image",
                        action="store_true")
    args = parser.parse_args()

    img=args.image
    if len(args.files)>0: img=args.files[0]
    
    if not os.path.isfile(img):
        print "image file not found"
        sys.exit()
    print "converting",img

    bkg=args.background
    if len(args.files)>1:
        bkg=args.files[1]
    print "subtracting background from",bkg

    tfname = os.path.basename(img).split(".tif")[0]+".root"
    if args.output: tfname=args.output
    tf=TFile(tfname,"recreate")
    print "Saving output to",tfname
    
    imagedat=tiff2TH2(img,bkg)
    #killhotpix(result)  # no good, spikes are not single pixels? coding?

    imagedat["hImage"].Write()
    imagedat["iVals"].Write()
    imagedat["iValsL"].Write()
    print "Wrote",tf.GetName()

    if args.display:
        display(imagedat)
