import os
import getopt
import sys
from PIL import Image

opts, args = getopt.getopt(sys.argv[1:], 'd:o:f:w:h:p:c:')
 
directory = ''
outputDir = ''
fileName = ''
width = ''
height = ''
padVal = ''
count = ''

# get user variables
for opt, arg in opts:
    if opt == '-d':
        directory = arg
    elif opt == '-o':
        outputDir = arg
    elif opt == '-f':
        fileName = arg
    elif opt == '-w':
        width = arg
    elif opt == '-h':
        height = arg
    elif opt == '-p':
        padVal = arg
    elif opt == '-c':
        count = arg

# set defaults
if width == '':
    width = '-1'
if height == '':
    height = '-1'
if padVal == '':
    padVal = '-1'
if count == '':
    count = '-1'

# error check and script help
if fileName == '' or directory == '' or outputDir == '':
    print('Invalid command line arguments. Usage python imageDataBaseCreator.py -d [input image directory] ' \
          '-o [output image directory] -f [new image file name] are required '\
	      '-w [resize width] -h [resize height] -p [padding value] -c [image start number] are optional')
    exit()

# set log output directory
logDir = fileName+'-scriptOutput'

# run step 1, 2, & 3 scripts to generate the dataBase
os.system('python step-1.py -d '+directory+' -o '+outputDir+' -f '+fileName +' -w '+ width +' -h '+height+' -p ' +padVal+' -c ' +count);
os.system('python step-2.py -d '+outputDir+' -f tag_file_name.txt');
os.system('python step-3.py -l script-labels.txt -t csv_tag_file_name.txt >> '+fileName+'-val.txt');

# remove  and copy system files and duplicates
from sys import platform as _platform
if _platform == "linux" or _platform == "linux2":
    print('imageDataBaseCreator.py Linux Detected')
    os.system('rm -rf tag_file_name.txt output.log');
    os.system('mv csv_tag_file_name.txt '+logDir+'/csv_tag_file_name.csv');
    os.system('cp '+fileName+'-val.txt '+logDir+'/'+fileName+'-val.txt');
elif _platform == "win32" or _platform == "win64":
    print('imageDataBaseCreator.py Windows Detected')
    os.system('DEL tag_file_name.txt output.log');
    os.system('rm -rf tag_file_name.txt output.log');
    os.system('mv csv_tag_file_name.txt '+logDir+'/csv_tag_file_name.csv');
    os.system('cp '+fileName+'-val.txt '+logDir+'/'+fileName+'-val.txt');

# generate error reports
orig_stdout = sys.stdout
sys.stdout = open(logDir+'/'+fileName+'-fileNameWithLabels.csv','a')
print('Old FileName, New FileName, Labels')
sys.stdout = open(logDir+'/'+fileName+'-fileNameWithErrors.csv','a')
print('Old FileName, New FileName')
sys.stdout = open(logDir+'/'+fileName+'-multipleLabelsFile.csv','a')
print('Old FileName, New FileName, Labels')
sys.stdout = open(logDir+'/'+fileName+'-invalidLabelsFile.csv','a')
print('Old FileName, New FileName, Labels')


# generate reports for images with and without labels
with open(logDir+'/'+fileName+'-FileNameTanslation.csv') as orig_filename:
    for file in orig_filename:
        fileList = file.strip().split(",")
        imgFileCount = 0
        sys.stdout = open(logDir+'/'+fileName+'-fileNameWithLabels.csv','a')
        with open(logDir+'/csv_tag_file_name.csv') as tagFile:
            for tag in tagFile:
                tagList = tag.strip().split(",")
                fileList[1] = fileList[1].strip()
                tagList[0] = tagList[0].strip()

                if fileList[1] == tagList[0]:
                    imgFileCount += 1
                    tag = tag.strip()
                    print(fileList[0]+','+tag)

        if imgFileCount == 0:
            sys.stdout = open(logDir+'/'+fileName+'-fileNameWithErrors.csv','a')
            print(fileList[0]+','+fileList[1])


# generate report for multiple labels for single image
with open(logDir+'/'+fileName+'-FileNameTanslation.csv') as orig_filename:
    for file in orig_filename:
        fileList = file.strip().split(",")
        multipleLabelFlag = 0
        sys.stdout = open(logDir+'/'+fileName+'-fileNameWithLabels.csv','a')
        with open(logDir+'/'+fileName+'-val.txt') as tagFile:
            for tag in tagFile:
                tagList = tag.strip().split(" ")
                fileList[0] = fileList[0].strip()
                fileList[1] = fileList[1].strip()
                tagList[0] = tagList[0].strip()
                tagList[1] = tagList[1].strip()

                if fileList[1] == tagList[0]:
                    multipleLabelFlag += 1

                if multipleLabelFlag > 1:
                    multipleLabelFlag = 0
                    sys.stdout = open(logDir+'/'+fileName+'-multipleLabelsFile.csv','a')
                    print(fileList[0]+','+tagList[0]+','+tagList[1])


# generate report for invalid labels for single image
sys.stdout = open(logDir+'/'+fileName+'-invalidLabelsFile.csv','a')
with open(logDir+'/'+fileName+'-FileNameTanslation.csv') as orig_filename:
    for file in orig_filename:
        fileList = file.strip().split(",")
        
        with open(logDir+'/'+fileName+'-val.txt') as tagFile:
            for tag in tagFile:
                tagList = tag.strip().split(" ")
                fileList[0] = fileList[0].strip()
                fileList[1] = fileList[1].strip()
                tagList[0] = tagList[0].strip()
                tagList[1] = tagList[1].strip()

                if fileList[1] == tagList[0] and tagList[1] == '-1':
                    with open(logDir+'/csv_tag_file_name.csv') as labelfilename:
                        for labelfile in labelfilename:
                            LABELfile = labelfile.strip().split(",")
                            if LABELfile[0] == tagList[0]:
                                labelfile = labelfile.strip()
                                print(fileList[0]+','+labelfile)

# remove  and copy system files and duplicates
from sys import platform as _platform
if _platform == "linux" or _platform == "linux2":
    os.system('rm -rf '+logDir+'/csv_tag_file_name.csv');
    os.system('rm -rf '+logDir+'/'+fileName+'-val.txt');
elif _platform == "win32" or _platform == "win64":
    os.system('DEL '+logDir+'/csv_tag_file_name.csv');
    os.system('DEL '+logDir+'/'+fileName+'-val.txt');
    os.system('rm -rf '+logDir+'/csv_tag_file_name.csv');
    os.system('rm -rf '+logDir+'/'+fileName+'-val.txt');
