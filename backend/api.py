
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
from sklearn.cluster import MeanShift,estimate_bandwidth,AffinityPropagation,KMeans
from skimage.color import rgba2rgb
import os
from flask_cors import CORS
def transpose(arr,doRF,doUV,ROIs):
    if doRF or doUV:
        num=2
    else:
        num=1
    for i in arr:
        i.reverse()
    answers = np.asarray(arr)
    arr2=[]
    arr2 = [[0 for x in range(len(answers))] for y in range(len(answers[0]))]
    for i in range(len(arr2)):
        for j in range(len(arr2[0])):
            arr2[i][j]=list(answers[j][i])
    arr2.reverse()
    
            
    
    return arr2
def find_RL_UD(img,centers):
    arr = []
    for center in centers:

        x,y=center[1],center[0]
        tim = time.time()
        
        LR = 0
        RR=0
        UR=0
        DR=0
        num_zeros = 0

        row = int(y)
        col = int(x)
        val = 2.1*np.mean(img)
        max_zeros = 10
        
        while num_zeros<max_zeros and LR<40 and col-LR>10:
            for i in range(round(-3),round(3)):
                
                if img[row+i][col-LR]<=val:
                    num_zeros+=1
            LR+=1
        num_zeros = 0
        while num_zeros<max_zeros and RR<40 and col+RR<682-10:
            for i in range(round(-3),round(3)):
                
                if img[row+i][col+RR]<=val:
                    num_zeros+=1
            RR+=1
        num_zeros = 0
        while num_zeros<max_zeros and UR<40 and row+UR<682-10:
            for i in range(round(-3),round(3)):
                
                if img[row+UR][col+i]<=val:
                    num_zeros+=1
            UR+=1
        num_zeros = 0
        while num_zeros<max_zeros and DR<40 and row-DR>10:
            for i in range(round(-3),round(3)):
                
                if img[row-DR][col+1]<=val:
                    num_zeros+=1
            DR+=1
        arr.append((round(center[0]+(UR-DR)/2),round(center[1]+(RR-LR)/2)))
    ##print(arr)
    return arr
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
                    i.insert(-1,["NA","NA"])
                else:
                    i.insert(-1,["NA"])
    ####print(arr)
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
def sort2(points2,index=0):
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
                if points2[i][j][index]<points2[i][k][index]:
                    
                    
                    a = points2[i][j]
                    points2[i][j]=points2[i][k]
                    points2[i][k] = a    
def makeTruePoints(points2,img):
    for b in range(len(points2)):
        rowRad,colRad = points2[b][2],points2[b][3]
        i = points2[b]
        xAv,yAv = computeXY_circle(img,i[0]-rowRad,i[0]+rowRad,i[1]-colRad,i[1]+rowRad)
        i = (xAv,yAv)
def predictLanes(ROIs,lanes):
    tim = time.time()
    xs = []
    for i in range(len(ROIs)):
        xs.append(ROIs[i][1])
    xs = np.asarray([xs])
    xs = xs.T
    thresh = KMeans(n_clusters=lanes).fit(xs).cluster_centers_
    np.sort(thresh)
    ##print(time.time()-tim)
    thresh =thresh.tolist()
    for i in thresh:
        i.insert(0,1)
    ##print(thresh)
    
    return thresh
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
def ROIs_from_points(points,tim):
    
    arr = []
    for i in range(len(points)):
        res = findRadius(tim,points[i][1],points[i][0],1)
       
        arr.append([points[i][1],points[i][0],res['rowRadius'],res['colRadius']])
    return arr
    

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
    ###print('dark')
    Dark = makeFileArray(Dark,Dark2)
    ###print('flat')
    Flat = makeFileArray(Flat,Flat2)
    ###print('cerenkov')
    Cerenkov = makeFileArray(Cerenkov,Cerenkov2)
    ###print('UV')
    UV = makeFileArray(UV,UV2)
    ##print('UVFLAt')
    UVFlat = makeFileArray(UVFlat,UVFlat2)
    ##print('b')
    Bright = makeFileArray(Bright,Bright2)
    ##print('bf')
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
def clear_near(centers):
    
    return centers
def findCenters(img):
    u = time.time()
    img=img.copy()

    img-= morphology.area_opening(img,area_threshold=3500)
    #print(time.time()-u)
    img = morphology.opening(img,morphology.rectangle(19,1))
    img=morphology.opening(img,morphology.rectangle(1,17))


    
    
    u=time.time()


    tim =time.time()
    img2 = morphology.h_maxima(img, 5)
    img2 = morphology.dilation(img2,morphology.disk(4))
    
    img2 = label(img2)

    num_things = round(np.max(img2))

    colors_arr = [[] for i in range(num_things)]
    for i in range(len(img2)):
        for j in range(len(img2[i])):
            if round(img2[i][j])!=0:
                colors_arr[round(img2[i][j]-1)].append((i,j))

    centers = []
    for i in range(len(colors_arr)):
        count=0
        totalcol= 0
        totalrow=0
        for j in colors_arr[i]:
            
            totalcol+=j[1]
            totalrow+=j[0]
            count+=1
        totalcol/=count
        totalrow/=count
        centers.append((int(totalrow),int(totalcol)))
    ###print(time.time()-u)
    #print(time.time()-u)
    centers=clear_near(centers)
    return centers
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
    
         
    Cerenkov = Cerenkov-Dark
    Cerenkov = Cerenkov/Flat
    Cerenkov = filters.median(Cerenkov)
    Cerenkov = transform.rotate(Cerenkov,270)
    t = time.time()
    ROIs=findCenters(Cerenkov)
    disk = morphology.disk(25)
    Cerenkov -= morphology.opening(Cerenkov,selem=disk)
    for i in range(4):
        ROIs = find_RL_UD(Cerenkov,ROIs)
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
        timee = time.time()
        UV -=morphology.opening(UV,morphology.disk(30))
        UV = UV**.65
        UV*=(np.max(Cerenkov))/(np.max(UV))
        UV_show = UV.copy()
    if doUV:
        UV_show= UV.copy()
        UV_show = UV_show-np.min(UV_show)
        UV_show = UV_show *1/np.max(UV_show)
        UV_show = Image.fromarray((np.uint8(plt.get_cmap('viridis')(UV_show)*255)))

    if  not doUV:
        display_img = Cerenkov.copy()
    if doUV:
        display_img=UV.copy()+Cerenkov
        display_img_calc = Cerenkov
    if not doUV:
        return display_img,Cerenkov,doUV,ROIs
    else:
        return display_img,display_img_calc,doUV,Cerenkov_show,UV_show,Cerenkov,ROIs
def isStorage(item):
    return("FileStorage" in str(type(item)))



def makeFileArray(fileN,fileN1):
    tim = time.time()
    try:
        fileN1 = np.loadtxt(fileN1)
        fileN = fileN1
        
    except:
        try:
            fileN = Image.open(fileN.stream)
            fileN = np.asarray(fileN)
        except:
            pass
    ###print(time.time()-tim)
    return fileN

app = Flask(__name__)
CORS(app)
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
            calc = img_cerenk[-2]
            np.save('./UPLOADS/'+tim+'calc.npy',calc)
        points = img_cerenk[-1]
        points = ROIs_from_points(points,tim)
        ##print(points)
        
        res = tim
        return {"res":res,"test_ROIS":points}

@app.route('/img/<filename>',methods = ['GET'])
def give(filename):
    filen = './UPLOADS/'+filename+'.png' 
    return send_file(filen)
@app.route('/radius/<filename>/<x>/<y>/<shift>',methods = ['GET'])
def findRadius(filename,x,y,shift):
    
    tim = time.time()
    img = np.load('./UPLOADS/'+filename+'.npy')
    rowRadius = 0
    colRadius = 0
    num_zeros = 0

    row = int(y)
    col = int(x)
    print(shift)
    if (shift=='0'):
        for i in range(3):
            center  = find_RL_UD(img,[(row,col)])
            row = center[0][0]
            col=center[0][1]
    val =(np.mean(img[:,150:len(img[0])-150]))
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
    return{"col":col,"row":row,"colRadius":colRadius,"rowRadius":rowRadius}
@app.route('/UV/<filename>',methods = ['GET'])
def giveUV(filename):
    filen = './UPLOADS/'+filename+'UV.png' 
    return send_file(filen)
@app.route('/Cerenkov/<filename>',methods = ['GET'])
def giveCerenkov(filename):
    filen = './UPLOADS/'+filename+'Cerenkov.png' 
    return send_file(filen)
@app.route('/database',methods = ['POST'])
def upload_data():
    
    
    np.save('./database/'+request.form["Cerenkovname"]+request.form["Darkname"]+request.form["Flatname"]+request.form["UVname"]+request.form["UVFlatname"],(request.form.to_dict()))
    return({"hi":1})
@app.route('/results/<filename>',methods = ['POST'])
def results(filename):
    tim = time.time()
    
    doUV = np.load('./UPLOADS/'+filename+'UV.npy')
    doUV = doUV[0]

    origins = request.form['origins']
    ROIs = request.form['ROIs']
    doRF = request.form['doRF']=='true'
    autoLane=request.form['autoLane']=='true' and (not doRF and not doUV)
    num_lanes=int(request.form['n_l'])
    #print(request.form['autoLane'])
    #print(request.form['autoLane']=='true' and (not doRF and not doUV))
    #print(autoLane)
    if not autoLane:
    
        #print('!')
        origins = np.asarray([int(i) for i in origins.split(',')])
    ROIs = np.asarray([int(j) for j in ROIs.split(',')])
    if not autoLane:
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
    if not autoLane:
        #print('!')
        for j in range(len(originsx)):
            newOrigins.append([originsy[j],originsx[j]])
    if doUV:
        img2 = np.load('./UPLOADS/'+filename+'.npy')
        img = np.load('./UPLOADS/'+filename+'calc.npy')
        newOrigins = [newOrigins]
        sort2(newOrigins,index =0)
        newOrigins=newOrigins[0]
        newOrigins = newOrigins[::-1]
        print(newOrigins)
        cerenks= calculateCerenkov(newROIs,newOrigins[:-2],img)
        RFs = calculateRF(newROIs,newOrigins,img2)
        cerenks_RFs=[]
        for i in range(len(cerenks)):
            lane = []
            for j in range(len(cerenks[i])):
                lane.append([cerenks[i][j][4],RFs[i][j][2]])
            cerenks_RFs.append(lane)
        makeUniform(cerenks_RFs)
        #print(list(zip(cerenks_RFs)))
        cerenks_RFs = transpose(cerenks_RFs,doUV,doRF,newROIs)
        ###print(cerenks_RFs)
        ###print(time.time()-tim)
        return {"arr":cerenks_RFs}
    elif doRF and not doUV:
        img = np.load('./UPLOADS/'+filename+'.npy')
        newOrigins = [newOrigins]
        sort2(newOrigins,index=0)
        newOrigins = newOrigins[0]
        newOrigins = newOrigins[::-1]
        print(newOrigins)
        cerenks = calculateCerenkov(newROIs,newOrigins[:-2],img)
        RFs = calculateRF(newROIs,newOrigins,img)
        cerenks_RFs=[]
        for i in range(len(cerenks)):
            lane = []
            for j in range(len(cerenks[i])):
                lane.append([cerenks[i][j][4],RFs[i][j][2]])
            cerenks_RFs.append(lane)
        makeUniform(cerenks_RFs)
        ###print(cerenks_RFs)
        #print(list(zip(cerenks_RFs)))
        cerenks_RFs = transpose(cerenks_RFs,doUV,doRF,newROIs)
        ###print(time.time()-tim)
        return {"arr":cerenks_RFs}
        
    else:
        img = np.load('./UPLOADS/'+filename+'.npy')
        if autoLane:
            newOrigins = predictLanes(newROIs,num_lanes)
        cerenks = calculateCerenkov(newROIs,newOrigins,img)
        
        cerenk_answers = []

        for i in range(len(cerenks)):
            lane = []
            for j in range(len(cerenks[i])):
                lane.append([cerenks[i][j][4]])
            cerenk_answers.append(lane)
        nparr = np.asarray(cerenk_answers)
        np.save('./UPLOADS/'+filename+'Answers.npy',nparr)
        makeUniform(cerenk_answers,doRF=False)
        
        ###print(cerenk_answers)
        #print(list(zip(cerenk_answers)))
        cerenk_answers = transpose(cerenk_answers,doUV,doRF,newROIs)
        #print(type(cerenk_answers))
        return{"arr":cerenk_answers}

if __name__ == '__main__':
    #print("Running!")
    app.run(host='0.0.0.0',debug=True,port=5000)

    


        

        

        
        

    
    
    

