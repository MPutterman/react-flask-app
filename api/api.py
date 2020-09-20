
import time
import base64
from flask import Flask, request,Response,send_file,send_from_directory,make_response,Response
from skimage import io, morphology, filters,transform, segmentation,exposure
from skimage.util import invert
import scipy
from matplotlib import pyplot as plt
from matplotlib import use,gridspec
from skimage.measure import label
from matplotlib.patches import Rectangle
from matplotlib.widgets import RectangleSelector, Button, EllipseSelector
import matplotlib.patches as pat
from matplotlib import interactive
import matplotlib
import numpy as np
from PIL import Image
from io import BytesIO
from skimage.color import rgba2rgb
import os
def findMaxLength(arr):
    lens = []
    for i in arr:
        lens.append(len(i))
    lens.sort()
    return lens[-1]
def makeUniform(arr,doRF = True):
    max_len = findMaxLength(arr)
    for i in arr:
        if len(i)<max_len:
            
            while len(i)<max_len:
                if doRF:
                    i.append(["NA","NA"])
                else:
                    i.append(["NA"])
    #print(arr)
def findClosest(arr1,arr2):
    theArr = []
    ar1 = np.asarray(arr1)
    ar2 = np.asarray(arr2)
    ar2_copy = ar2.copy()
    for i in range(len(ar1)):
        ar2 = ar2_copy.copy()
        ar2 -= ar1[i]
        ar2 = abs(ar2)
        theArr.append(np.argsort(ar2)[0])
    return theArr
def computeXY_circle(img,rowMin,rowMax,colMin,colMax,multiply_place=True):
    colRadiusSquared = ((colMax-colMin)/2)**2
    rowRadiusSquared = ((rowMax-rowMin)/2)**2
    rowCent = (rowMax+rowMin)/2
    colCent = (colMax+colMin)/2
    rowTotal = 0
    colTotal = 0
    pixelCount = 0
    
    for row in range(int(.9*int(min(rowMin,rowMax))),int(max(rowMin,rowMax)+.1*(len(img)-max(rowMin,rowMax)))):
        for col in range(int(.9*int(min(colMin,colMax))),int(max(colMin,colMax)+.1*(len(img[0])-max(colMin,colMax)))):
            if ((row-rowCent)**2)/(rowRadiusSquared)+(((col-colCent)**2)/colRadiusSquared)<=1.1:
                if multiply_place:
                    rowTotal += row*img[row][col]
                    colTotal += col*img[row][col]
                else:
                    rowTotal+=img[row][col]
                    colTotal+=img[row][col]
                pixelCount +=1

    if not multiply_place:
        pixelCount = 1
    return(rowTotal/pixelCount,colTotal/pixelCount)
def sort2(points2):
    """Sorts points2 by simple bubblesort
    Args:
        points2(list)
    Mutates:
        points2(list)
    """
    u = points2
    for i in range(len(points2)):
        for j in range(len(points2[i])):
            for k in range(len(points2[i])):
                if points2[i][j][0]<points2[i][k][0]:
                    
                    
                    a = points2[i][j]
                    points2[i][j]=points2[i][k]
                    points2[i][k] = a    
def makeTruePoints(points2,img):
    for b in range(len(points2)):
        rowRad,colRad = points2[b][2],points2[b][3]
        i = points2[b]
        xAv,yAv = computeXY_circle(img,i[0]-rowRad,i[0]+rowRad,i[1]-colRad,i[1]+rowRad)
        i = (xAv,yAv)
def calculateRF(points2,points,img):
    makeTruePoints(points2,img)
    p1,p2 = points[-2],points[-1]
    if p2[0]-p1[0]!=0:
        SlopeInvTop = (p2[1]-p1[1])/(p2[0]-p1[0])
    else:
        SlopeInvTop=5000
    isTopNeg = SlopeInvTop/abs(SlopeInvTop)
    rowT = int(p1[0]-isTopNeg*(p1[1]//SlopeInvTop))
    
    points = points[:-2]

    points2_copy = []
    points2_copy2 = []
    for i in range(len(points2)):
        points2_copy2.append(points2[i])
        points2_copy.append(points2[i][1])
    points2 = points2_copy
    thresholds = []
    for i in range(len(points)):
        thresholds.append(points[i][1])
    thresholds.sort()
    whatLane = findClosest(points2,thresholds)
    #whatLane = orgranize each center into which lane it should be in
    points3 = [[0]*1 for i in range(len(points))]
    #create an array points2 which has lane rows

    for spot in range(len(points2)):
        #  two points = 1 rectangle, which is why its len(points)//2
        
        where = whatLane[spot]
        # set where variable equal to whatLane a certain rectangle should be in
        
        points3[where].append(spot)
        # at that lane, append which rectangle it is

    for l in range(len(points3)):
        points3[l] = points3[l][1:]
        # take away the zero at the beginning of each lane
    for l in range(len(points3)):
        for j in range(len(points3[l])):
            # for every cell in point2, change it to the corresponding 
            spot = points3[l][j]
            points3[l][j] = (points2_copy2[spot])
    sort2(points3)
    for lane in range(len(points3)):
        for spot in range(len(points3[lane])):
            point_row,point_col = points3[lane][spot][0],points3[lane][spot][1]
            origin_row,origin_col = points[lane][0],points[lane][1]
            if point_col-origin_col!=0:

                SlopeOfLine = (((point_row)-(origin_row))/(point_col-origin_col))
            else:
                SlopeOfLine = 1000
            SlopeOfOtherLine = 1/SlopeInvTop
            intercept = point_row-(point_col*SlopeOfLine)
            intercept_other = rowT
            finalSlope = SlopeOfLine-SlopeOfOtherLine
            finalIntercept = intercept_other-intercept
            theCol = int(finalIntercept/finalSlope)
            theRow = int(SlopeOfOtherLine*theCol+intercept_other)
            dist = findDistance(theCol,theRow,origin_col,origin_row)
            partialDistance = findDistance(point_col,point_row,origin_col,origin_row)
            RF = partialDistance/dist
            points3[lane][spot]=(points3[lane][spot][0],points3[lane][spot][1],round(RF,2))
    return points3
def findDistance(col1,row1,col2,row2):
    return(((col2-col1)**2+(row2-row1)**2)**.5)

def calculateCerenkov(newArr,thresholds,img):
    newArr_copy = []
    newArr_copy2 = []
    for i in range(len(newArr)):
        newArr_copy2.append(newArr[i])
        newArr_copy.append(newArr[i][1])
    newArr = newArr_copy
    for i in range(len(thresholds)):
        thresholds[i] = (thresholds[i][1])
    thresholds.sort() 
    whatLane = findClosest(newArr,thresholds)
    #whatLane = orgranize each center into which lane it should be in
    final_arr = [[0]*1 for i in range(len(thresholds))]
    #create an array newArr which has lane rows

    for spot in range(len(newArr)):
        #  two thresholds = 1 rectangle, which is why its len(thresholds)//2
        
        where = whatLane[spot]
        # set where variable equal to whatLane a certain rectangle should be in
        
        final_arr[where].append(spot)
        # at that lane, append which rectangle it is

    for l in range(len(final_arr)):
        final_arr[l] = final_arr[l][1:]
        # take away the zero at the beginning of each lane

    for l in range(len(final_arr)):
        for j in range(len(final_arr[l])):
            # for every cell in point2, change it to the corresponding 
            spot = final_arr[l][j]

            final_arr[l][j] = (newArr_copy2[spot])
    sort2(final_arr)
    for lane in range(len(final_arr)):   
        total_totals = 0
        for spot in range(len(final_arr[lane])):
            row_num = final_arr[lane][spot][0]
            col_num = final_arr[lane][spot][1]
            row_rad = final_arr[lane][spot][2]
            col_rad = final_arr[lane][spot][3]
            total = computeXY_circle(img,row_num-row_rad,row_num+row_rad,col_num-col_rad,col_num+col_rad,multiply_place = False)[0]
            total_totals+=total
        for spot in range(len(final_arr[lane])):
            row_num = final_arr[lane][spot][0]
            
            col_num = final_arr[lane][spot][1]
            row_rad = final_arr[lane][spot][2]
            col_rad = final_arr[lane][spot][3]
            total = computeXY_circle(img,row_num-row_rad,row_num+row_rad,col_num-col_rad,col_num+col_rad,multiply_place = False)[0]
            final_arr[lane][spot] = (row_num,col_num,row_rad,col_rad,total/total_totals)
    return final_arr
def finalize(Dark,Dark2,Flat,Flat2,Cerenkov,Cerenkov2,UV,UV2,UVFlat,UVFlat2,Bright,Bright2,BrightFlat,BrightFlat2):
    
    Dark = makeFileArray(Dark,Dark2)
    Flat = makeFileArray(Flat,Flat2)
    Cerenkov = makeFileArray(Cerenkov,Cerenkov2)
    UV = makeFileArray(UV,UV2)
    UVFlat = makeFileArray(UVFlat,UVFlat2)
    Bright = makeFileArray(Bright,Bright2)
    BrightFlat = makeFileArray(BrightFlat,BrightFlat2)
    if isStorage(Cerenkov):
        Cerenkov = np.loadtxt('./SampleData/DMSO140-160')
    if isStorage(Dark):
        Dark= Image.open('./SampleData/masterdark.tiff')
        Dark = np.asarray(Dark)
        
    if isStorage(Flat):
        Flat= Image.open('./SampleData/masterflat.tiff')
        Flat = np.asarray(Flat)
    return startUp(Dark,Flat,Cerenkov,UV,UVFlat,Bright,BrightFlat)
def startUp(Dark,Flat,Cerenkov,UV,UVFlat,Bright,BrightFlat):
    doUV = True
    
    if int(isStorage(UV))  +int(isStorage(Bright)) ==1:
        if isStorage(UV):
            UV = Bright
            UVFlat = BrightFlat
        else:
            Bright = UV
            BrightFlat = UVFlat
    if (isStorage(UV)) and (isStorage(Bright)):
        doUV = False
        
        
    if doUV:
        if isStorage(UVFlat) and isStorage(BrightFlat):
            UVFlat = np.zeros_like(UV)+1
    if doUV:
        Cerenkov = transform.rotate(Cerenkov,180) 
    Cerenkov = Cerenkov-Dark
    Cerenkov = Cerenkov/Flat
    Cerenkov = filters.median(Cerenkov)
    Cerenkov = transform.rotate(Cerenkov,90)
    
    disk = morphology.disk(25)
    Cerenkov -= morphology.opening(Cerenkov,selem=disk)
    Cerenkov-=np.min(Cerenkov)
    if doUV:
        Cerenkov_show= Cerenkov.copy()
        Cerenkov_show = Cerenkov_show-np.min(Cerenkov_show)
        Cerenkov_show = Cerenkov_show *1/np.max(Cerenkov_show)
        Cerenkov_show = Image.fromarray((np.uint8(plt.get_cmap('viridis')(Cerenkov_show)*255)))
    if doUV:
        UV/=UVFlat
        UV = transform.rotate(UV,270)
        UV = filters.median(UV)
        UV = (np.max(UV)-UV)
        UV-=np.min(UV)
        UV *= ((np.max(Cerenkov)-np.min(Cerenkov))/(np.max(UV)-np.min(UV)))
        UV= morphology.closing(UV,selem=morphology.disk(8))
        UVCopy_display = UV.copy()
        UV-=morphology.opening(UV,selem=morphology.disk(35))
        UV_show = UV.copy()
    if doUV:
        UV_show= UV.copy()
        UV_show = UV_show-np.min(UV_show)
        UV_show = UV_show *1/np.max(UV_show)
        UV_show = Image.fromarray((np.uint8(plt.get_cmap('viridis')(UV_show)*255)))

    if  not doUV:
        display_img = Cerenkov.copy()
    if doUV:
        display_img=UVCopy_display+Cerenkov
        Cerenkov = Cerenkov+UV.copy()
    if not doUV:
        return display_img,Cerenkov,doUV
    else:
        return display_img,Cerenkov,doUV,Cerenkov_show,UV_show
def isStorage(item):
    return("FileStorage" in str(type(item)))



def makeFileArray(fileN,fileN1):
    try:
        fileN1 = np.loadtxt(fileN1)
        fileN = fileN1
        
    except:
        try:
            fileN = Image.open(fileN.stream)
            fileN = np.asarray(fileN)
        except:
            pass
    return fileN

app = Flask(__name__)
@app.route('/time', methods = ['POST','GET'])

def createFile():
    if request.method == 'POST':
        
        Dark = request.files['Dark']
        Dark2 = request.files['Dark']
        Flat = request.files['Flat']
        Cerenkov = request.files['Cerenkov']
        UV = request.files['UV']
        UVFlat = request.files['UVFlat']
        Bright = request.files['Bright']
        BrightFlat = request.files['BrightFlat']
        Flat2 = request.files['Flat']
        Cerenkov2 = request.files['Cerenkov']
        UV2 = request.files['UV']
        UVFlat2 = request.files['UVFlat']
        Bright2 = request.files['Bright']
        BrightFlat2 = request.files['BrightFlat']
        
        tim = str(int(time.time()))
        img_cerenk = finalize(Dark,Dark2,Flat,Flat2,Cerenkov,Cerenkov2,UV,UV2,UVFlat,UVFlat2,Bright,Bright2,BrightFlat,BrightFlat)
        Cerenkov = img_cerenk[1]
        np.save("./UPLOADS/"+tim+'.npy',Cerenkov)
        img = img_cerenk[0]
        doUV = img_cerenk[2]
        np.save("./UPLOADS/"+tim+'UV.npy',np.asarray([doUV]))
        

        img = img-np.min(img)
        img = img *1/np.max(img)
        img = Image.fromarray((np.uint8(plt.get_cmap('viridis')(img)*255)))
        filepath = './UPLOADS/'+tim+'.png'
        img.save(filepath)
        if doUV:
            Cerenkov_show = img_cerenk[3]
            UV_show = img_cerenk[4]
            Cerenkov_show.save('./UPLOADS/'+tim+'Cerenkov.png')
            UV_show.save('./UPLOADS/'+tim+'UV.png')
        
        res = tim
        return res

@app.route('/img/<filename>',methods = ['GET'])
def give(filename):
    filen = './UPLOADS/'+filename+'.png' 
    return send_file(filen)
@app.route('/radius/<filename>/<x>/<y>',methods = ['GET'])
def findRadius(filename,x,y):
    
    tim = time.time()
    img = np.load('./UPLOADS/'+filename+'.npy')
    rowRadius = 0
    colRadius = 0
    num_zeros = 0

    row = int(y)
    col = int(x)
    ##print(img[row][col])
    #print('1',np.mean(img))
    val =(np.mean(img[:,150:len(img[0])-150]))
    #print(col)
    #print('2',val)
    #print('3',img[20][20])
    #print('4',img[200][350])
    max_zeros = 25
    thickness = 8
    while num_zeros<max_zeros and row+rowRadius<len(img) and row-rowRadius>0:
        for i in range(round(-thickness/2),round(thickness/2)):
            if img[(row+rowRadius)][(col+i)] <=val:
                    num_zeros +=1
            if img[row-rowRadius][col+i]<=val:
                num_zeros+=1
        rowRadius+=1
    num_zeros = 0
    while num_zeros<max_zeros and col+colRadius<len(img) and col-colRadius>0:
        for i in range(round(-thickness/2),round(thickness/2)):
            if img[row+i][col+colRadius] <= val:
                num_zeros +=1
            if img[row+i][col-colRadius] <=val:
                num_zeros+=1
        colRadius+=1
    rowRadius,colRadius = max(rowRadius,14),max(colRadius,14)
    return{"colRadius":colRadius,"rowRadius":rowRadius}
@app.route('/UV/<filename>',methods = ['GET'])
def giveUV(filename):
    filen = './UPLOADS/'+filename+'UV.png' 
    return send_file(filen)
@app.route('/Cerenkov/<filename>',methods = ['GET'])
def giveCerenkov(filename):
    filen = './UPLOADS/'+filename+'Cerenkov.png' 
    return send_file(filen)
@app.route('/results/<filename>',methods = ['POST'])
def results(filename):
    tim = time.time()
    img = np.load('./UPLOADS/'+filename+'.npy')
    doUV = np.load('./UPLOADS/'+filename+'UV.npy')
    doUV = doUV[0]

    origins = request.form['origins']
    ROIs = request.form['ROIs']
    origins = np.asarray([int(i) for i in origins.split(',')])
    ROIs = np.asarray([int(j) for j in ROIs.split(',')])
    originsx = origins[::2]
    
    originsy=origins[1::2]
    ROIsx = ROIs[::4]
    ROIsy = ROIs[1::4]
    ROIsry = ROIs[2::4]
    ROIsrx = ROIs[3::4]
    newROIs = []
    newOrigins = []
    for i in range(len(ROIsx)):
        newROIs.append([ROIsy[i],ROIsx[i],ROIsry[i],ROIsrx[i]])
    for j in range(len(originsx)):
        newOrigins.append([originsy[j],originsx[j]])
    if doUV:
        cerenks= calculateCerenkov(newROIs,newOrigins[:-2],img)
        RFs = calculateRF(newROIs,newOrigins,img)
        cerenks_RFs=[]
        for i in range(len(cerenks)):
            lane = []
            for j in range(len(cerenks[i])):
                lane.append([cerenks[i][j][4],RFs[i][j][2]])
            cerenks_RFs.append(lane)
        makeUniform(cerenks_RFs)
        #print(cerenks_RFs)
        #print(time.time()-tim)
        return {"arr":cerenks_RFs}
    else:
        cerenks = calculateCerenkov(newROIs,newOrigins,img)
        
        cerenk_answers = []

        for i in range(len(cerenks)):
            lane = []
            for j in range(len(cerenks[i])):
                lane.append([cerenks[i][j][4]])
            cerenk_answers.append(lane)
        makeUniform(cerenk_answers,doRF=False)
        #print(cerenk_answers)
        return{"arr":cerenk_answers}

    


        

        

        
        

    
    
    

