import subprocess
import io
import os
from os.path import join
import sys

# Imports the Google Cloud client library
from google.cloud import vision_v1
from google.cloud.vision_v1 import types
# Instantiates a client
client = vision_v1.ImageAnnotatorClient()

fps = 0
fps1 = 0
videoFileName = os.path.splitext(os.path.basename(sys.argv[1]))[0]
genre=sys.argv[2]

def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)

################################################Code to extract Frames at 1fps ##########################################
def extractFramesAs1fps(videoName):
	print("extractFramesAs1fps=>"+videoName)
	outputPath = videoFileName+'_sample/'
	createFolder(outputPath)
	subprocess.call('ffmpeg -i '+ videoName + ' -vf fps=1 ./'+outputPath+'%0d.jpg -hide_banner') 

################################################Code to extract All Frames at actual fps ##################################
def extractAllFrames(videoName):
	outputPathAll = videoFileName+'_all/'
	createFolder(outputPathAll)
	subprocess.call('ffmpeg -i '+ videoName + ' ./'+outputPathAll+'%0d.jpg -hide_banner') 

################################################Code to Process image samples using cloud vision ##################################
def cloudVisionProcess (type_genre):
    #open a tmp file to dump the indexs of sample frame's which identified having adult/racy/violent content
    samplepath = videoFileName+'_sample/'
    obj_list=open(videoFileName+'_object_list.txt', "w+")
    obj_url = open(videoFileName + '_object_url.txt', "w+")
    for (dirname, dirs, files) in os.walk(samplepath):
        for filename in files:
            if filename.endswith('.jpg') :
                thefile = os.path.join(dirname,filename)
                # Loads the image into memory
                with io.open(thefile, 'rb') as image_file:
                    content = image_file.read()
                image = types.Image(content=content)
                objects = client.object_localization(image=image).localized_object_annotations
    print('Number of objects found: {}'.format(len(objects)))
    for object_ in objects:
        obj_list.write(str(object_.name))
        obj_list.write("\n")
        print('\n{} (confidence: {})'.format(object_.name, object_.score))
        print('Normalized bounding polygon vertices: ')
        for vertex in object_.bounding_poly.normalized_vertices:
            print(' - ({}, {})'.format(vertex.x, vertex.y))
    obj_list.close()

    #Eliminating duplicate objects
    scanned_objects = set()
    unique_obj_list = open(videoFileName + '_object_list_unique.txt', "w+")
    for line in open(videoFileName + '_object_list.txt', "r"):
        if line not in scanned_objects:
            unique_obj_list.write(line)
            scanned_objects.add(line)
            url_amzn = "https://www.amazon.in/" + line.strip("\n") + "/s?k=" + line.strip("\n")
            url_fkart = "https://www.flipkart.com/search?q=" + line.strip("\n")
            print(url_amzn)
            print(url_fkart)
            obj_url.write(url_amzn+"\n")
            obj_url.write(url_fkart+"\n")
    unique_obj_list.close()
    obj_url.close()

    #os.rename(videoFileName + '_object_url.txt', videoFileName + '_object_url.html')

extractFramesAs1fps(sys.argv[1])
extractAllFrames(sys.argv[1])
cloudVisionProcess(genre)

