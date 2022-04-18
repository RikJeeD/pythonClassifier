##########################################
import numpy as np
import matplotlib.pyplot as plt
from gdalconst import*
import osgeo.gdal as gdal

#############funcion para generar tif de salida##############
def guardar_tif(salida, matriz, im_entrada): #nom_salida, matriz de radiancia, banda de entrada
	#Definir coordenadas iniciales raster y resoluciones
	geoTs = im_entrada.GetGeoTransform() # 6 parámetros [ulx,resx(+),0,uly,0,resy(-)] resY(-) lat disminuye
	driver = gdal.GetDriverByName("GTiff") #Voy a manejar un tiff
	prj = im_entrada.GetProjection()  #Consulto la proyección al tif inicial
	cols = im_entrada.RasterXSize #Consulto columnas
	filas = im_entrada.RasterYSize #Consulto filas
	#Crear el espacio
	export=driver.Create(salida,cols,filas,1,GDT_Float64) #Escribir tif, nombre, cols,filas,num_bandas,tipo_dato (float)
	banda=export.GetRasterBand(1) #Cargo la banda creada en el paso anterior
	banda.WriteArray(matriz) #Escribe la matriz de radiancia
	export.SetGeoTransform(geoTs) #Asigna los parametros de la transformacion a la salida
	export.SetProjection(prj) #definir proyeccion
	banda.FlushCache()#descargar de la memoria virtual al disco
	export.FlushCache()#descargar de la memoria virtual al disco

##############funcion para calcular radiancia####################

def rad_l5(lmax,lmin,qcalmax,qcalmin,dn):
	rad = ((lmax-lmin)/(qcalmax-qcalmin))*(dn-qcalmin)+lmin
	return rad


##############funcion para calcular refelctancia################

def refl_l5(L,nband,cos_teta,k):
	pos = nband-1
	ESUN = [1997,1812,1533,1039,230.8,'N/A',84.90]
	refl = np.pi*L*k/(ESUN[pos]*cos_teta)
	return refl

##############funcion para temp de brillo################

def tb_l5(b):
    k12 = [607.76, 1260.56]
    tb= (k12[1])/np.log(k12[0]/b+1)
    return tb 

##############funcion cargar metadatos en diccionario############

def build_data(arc):
	output = {} #Diccionario vacío
	for line in arc.readlines(): #leemos cada línea del archivo
		if "=" in line: #si la línea tiene un '=' es porque es una variable de los metadatos
			l = line.split("=") #cortamos la línea en el ' = '
			# Llenamos el diccionario donde el primer elemento es el nombre de la variable, el segundo el valor
			output[l[0].strip()] = l[1].strip()
	return output #Retorna el diccionario con los pares de datos (variable = valor).

#####################script#####################################

path_meta = "C:/Users/Lenovo/Desktop/LE07_L1TP_009054_20120806_20161130_01_T1/"
path_img = "C:/Users/Lenovo/Desktop/LE07_L1TP_009054_20120806_20161130_01_T1/"
path_sal = "C:/Users/Lenovo/Desktop/LE07_L1TP_009054_20120806_20161130_01_T1/Salidas/"
meta = "LE07_L1TP_009054_20120806_20161130_01_T1_MTL.txt"

a = open(path_meta+meta,'r') #abrimos el archivo de los metadatos
data = build_data(a) #ejecutamos la función para que nos retorne el diccionario con los metadatos
a.close() #cerramos el archivo


for i in range(2,5):	 #iteramos en las 6 bandas recordando que el último elemento no se toma
	print "\n Calculando banda: LE07_L1TP_009054_20120806_20161130_01_T1_B"+str(i)
	if i != 6:
        #Cargamos la banda
		# se podría obtener el nombre "LT50090581999191CPE07" del parámetro
		# "LANDSAT_SCENE_ID" contenido en los metadatos... De esta forma tendríamos:
		# banda = gdal.Open(path_img+data['LANDSAT_SCENE_ID']+"_B"+str(i)+".TIF")
		banda = gdal.Open(path_img+"LE07_L1TP_009054_20120806_20161130_01_T1_B"+str(i)+".TIF")
		dn = banda.GetRasterBand(1).ReadAsArray().astype('float')
		background = [dn==0]
		dn[background] = np.nan
		#Cargamos los parámetros para el cálculo de la radiancia de esa banda
		lmax = float(data['RADIANCE_MAXIMUM_BAND_'+str(i)])
		lmin = float(data['RADIANCE_MINIMUM_BAND_'+str(i)])
		qcalmax = float(data['QUANTIZE_CAL_MAX_BAND_'+str(i)])
		qcalmin = float(data['QUANTIZE_CAL_MIN_BAND_'+str(i)])
		#Ejecutamos la función para calcular la radiancia
		radiancia = rad_l5(lmax,lmin,qcalmax,qcalmin,dn) #Matriz de radiancia
		#Cargamos los parámetros para el cálculo de la reflectancia de esa banda
		diajul = int(data['LANDSAT_SCENE_ID'][-9:-6]) #Día juliano
		angZS = 90-float(data['SUN_ELEVATION']) #ángulo cenital solar = 90-ángulo de elevación solar
		angZS_rad = angZS*np.pi/180 #ángulo en radianes
		cos_teta = np.cos(angZS_rad) #coseno de teta
		k = 1+0.0167*(np.sin(2*np.pi*(diajul-93.5)/365)**2) #Distancia tierra-sol
		#Ejecutamos la función para calcular la reflectancia
		reflectancia = refl_l5(radiancia,i,cos_teta,k) #Matriz de reflectancia
		refl_corr =reflectancia-np.nanmin(reflectancia) 
		#Salidas para cada imagen
		salida_rad = path_sal+"Radiancia/LE07_L1TP_009054_20120806_20161130_01_T1_B"+str(i)+"_rad.TIF"
		salida_ref = path_sal+"Reflectancia/"+"LE07_L1TP_009054_20120806_20161130_01_T1_B"+str(i)+"_ref.TIF"
		salida_ref_corat = path_sal+"Reflectancia/"+"LE07_L1TP_009054_20120806_20161130_01_T1_B"+str(i)+"_ref_corat.TIF"
		#Guardamos las imágenes de radiancia y reflectancia en formato tiff
		guardar_tif(salida_rad, radiancia, banda)
		guardar_tif(salida_ref, reflectancia, banda)
		guardar_tif(salida_ref_corat, refl_corr, banda)
		#A modo de verificación cargamos los valores utilizados para cada banda
		#y los comparamos con el archivo de metadatos
		#print "\nbanda: %s"%str(i)
	else:
		#calculo de temperatura de brillo
		banda6 = gdal.Open(path_img+"LE07_L1TP_009054_20120806_20161130_01_T1_B"+str(i)+".TIF")
		ds = banda6.GetRasterBand(1).ReadAsArray()
		temp_brillo = tb_l5(ds)
		salida_brillo = path_sal+"Radiancia/LE07_L1TP_009054_20120806_20161130_01_T1_B"+str(i)+"_brillo.TIF"
		guardar_tif(salida_brillo, temp_brillo, banda6)

