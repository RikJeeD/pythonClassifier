# -*- coding: utf-8 -*-

#Importando librerias necesarias#
from sklearn import cluster
from osgeo import gdal
import numpy as np
import matplotlib.pyplot as plt
import os

#Obteniendo imagen a clasificar#
dataset = gdal.Open(r"C:\Users\Andrés\Desktop\LC08_L1TP_007052_20190516_20190521_01_T1\LC08_L1TP_007052_20190516_20190521_01_T1_B2.TIF")
band = dataset.GetRasterBand(1)
img = band.ReadAsArray()
X = img.reshape((-1, 1))

#Realizando el K-means
k_means = cluster.KMeans(n_clusters=5)
_ = k_means.fit(X)

#Creando vista preliminar
X_clustered = k_means.labels_
X_clustered = X_clustered.reshape(img.shape)

plt.figure(figsize=(20,20))
plt.imshow(X_clustered, cmap="hsv")
plt.show()


#No sé para que sirve XD#
driver = gdal.GetDriverByName('GTiff')
x_size = array.shape[1]
y_size = array.shape[0]
dataset = driver.Create(filename, x_size, y_size, eType=gdal.GDT_Float32)
_ = dataset.GetRasterBand(1).WriteArray(X_clustered)


#Funcion para guardar
def guardar_tif(salida,matriz,im_entrada,x_in=0,y_in=0):
    #Definir coordenadas iniciales
    geoTs=im_entrada.GetGeoTransform()      #parametros
    driver=gdal.GetDriverByName("GTiff")
    prj=im_entrada.GetProjection()          #Proyeccion de la imagen de entrada     
    cols=matriz.shape[1]                    #Filas 
    filas=matriz.shape[0]                   #Columnas            
    ulx=geoTs[0]+x_in*geoTs[1]
    uly=geoTs[3]+y_in*geoTs[5]
    geoTs=(ulx,geoTs[1],geoTs[2],uly,geoTs[4],geoTs[5])
    #Crear el archivo con los datos de entrada
    export=driver.Create(salida,cols,filas,1,gdal.GDT_Float32)
    banda=export.GetRasterBand(1)
    banda.WriteArray(matriz)
    export.SetGeoTransform(geoTs)
    export.SetProjection(prj)
    banda.FlushCache()
    export.FlushCache()

#Guardando y creando salida
carpeta_resultados=(r"C:\Users\Andrés\Desktop\LC08_L1TP_007052_20190516_20190521_01_T1\carpeta_resultados")
os.mkdir(carpeta_resultados)
salida_clasificacion= (carpeta_resultados+os.sep+"clasificacionKMEANS.TIF")

guardar_tif(salida_clasificacion,X_clustered,dataset)
