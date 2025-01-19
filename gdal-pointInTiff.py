#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb  7 00:09:07 2021

@author: yoba
"""

import numpy as np
from osgeo import gdal
from numpy.linalg import inv as inverse
import pandas as pd


'''
  Parameters:
     
'''

tifZipFile='../ref/belgium_clc.zip'
tifFile='belgium_clc.tif'
fileContainingXYCoordinates='../input/sample-from-best-3035.zip'
fileContainingXYCoordinatesMergedWithTiff='../output/sample-from-best-3035-with-clc.zip'
compression_opts = dict(method='zip', archive_name='sample-from-best-3035-with-clc.csv')

tifZipFile='../ref/belgium_dem_v11.zip'
tifFile='belgium_dem_v11.tif'
fileContainingXYCoordinates='../input/sample-from-best-3035.zip'
fileContainingXYCoordinatesMergedWithTiff='../output/sample-from-best-3035-with-dem.zip'
compression_opts = dict(method='zip', archive_name='sample-from-best-3035-with-dem.csv')

'''
   Use gdal's virtual file system to access a tif inside a zip.
   
   See: https://gdal.org/user/virtual_file_systems.html
'''  

  
myRaster = gdal.Open(f'/vsizip/{tifZipFile}/{tifFile}')
#myRaster = gdal.Open(f'{tifFile}')

    
'''
 "Connect" to first band and tranform it into a matrix.
 
 There is only one band in our Corine Land Cover file, but other
 geotiffs might have multiple bands.
 
 The object returned by ReadAsAssay() is a numpy array:
     
 >> type(myBand)
 >> numpy.ndarray
 
 The numpy array can be very large. You can get the size of the array
 using myBand.shape. In this example, the size of the matry is:
     
 >> myBand.shape
 >> (2752, 3247)
 
 
''' 
 
myBand=myRaster.GetRasterBand(1).ReadAsArray()

'''
 Extract metadata from raster file.
 
 See: https://gdal.org/user/raster_data_model.html#affine-geotransform
 
 The metadata makes it possible to create a matrix to
 transform (pixel,line) coordinates into (x,y) georeferenced space.
 
 In our example, the pixel2xy matrix will transform (pixel,line) coordinates 
 of belgium_clc.tif into (x,y) coordinates in the EPSG:3035 projection system.
 
'''
 
M=myRaster.GetGeoTransform()

pixel2xy=np.array([[M[1], M[4]], 
                   [M[2], M[5]]])

translation=np.array([M[0],M[3]])


'''
 Compute "xy2pixel", ie, the inverse affine transformation matrix.
 
 This "xy2pixel" matrix can be used to convert (x,y) coordinates
 into (pixel,line) coordinates. 
 
'''

xy2pixel=inverse(pixel2xy)
    
'''
 Import a file containing (x,y) coordinates into a Pandas dataframe.
'''

adresses=pd.read_csv(f'{fileContainingXYCoordinates}',sep=',')

'''
 Convert into numpy array (matrix) and apply transformation
'''

xy=np.array(adresses[['x','y']])

pl = (xy-translation) @ xy2pixel 

pl=pd.DataFrame(pl,columns=['p','l'])

lmax,pmax=myBand.shape

'''
 Extract information from matrix 
'''

def extractInfoFor(l,p):
    if l>=0 and l<lmax and p>=0 and p<pmax:
        return myBand[int(l),int(p)]
    else:
        return -9999

adresses['value']=pl.apply(lambda row: extractInfoFor(row.l,row.p),axis=1)

'''
 Export results
'''

adresses.to_csv(f'{fileContainingXYCoordinatesMergedWithTiff}',
                sep='|',
                index=False,
                compression=compression_opts)