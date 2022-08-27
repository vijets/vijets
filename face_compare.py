# USAGE
# python recognize_faces_image.py --encodings encodings.pickle --image examples/example_01.png

# import the necessary packages
import face_recognition
import argparse
import pickle
import cv2
import os
import io
import json
import requests
import urllib
import urllib.parse
import numpy as np
from PIL import Image
import scipy.misc
import matplotlib
from io import StringIO
import base64
import encode_faces
import recognize_faces_image
import configparser
import detect_faces
import trail_process
#import unknown_image_trail_process
# import Image

# 1. Parse the input json object from the Kafka server.
# 2. Given contentId check if encodings is already available in the memory, if not, create a new one.
# 3. Given contentId if encodings are not available, fetch the actors list and corresponding images(from mongodb service) to generate a fresh set of encodings.
# 4. once the encodings are available, go ahead with the comparison process.[After creating the CNN/HOG encoding for the i/p frame].
# 5. update the mongodb service exposed using REST update call.


def storeFrameInputData(actors,contentId,playbackTime,inputImage_path,sample_db_available):
	#print("printing values inside storeFrameInputData")
	#print(actors)
	#print(contentId)
	#print(playbackTime)

	config = configparser.ConfigParser()
	config.read('config.ini')
	confidence = config['DNN_CONFIGS'] ['CONFIDENCE']
	caffefile = config['DNN_CONFIGS'] ['CAFE']
	protoxtfile = config['DNN_CONFIGS'] ['PROTOXT']
	if (detect_faces.image_detections(inputImage_path, protoxtfile, caffefile, confidence) == True):
		if (sample_db_available == False):
        #jump to trial process
			image = cv2.imread(inputImage_path)
			rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
			boxes = face_recognition.face_locations(rgb,
				model='HOG')
			encodings = face_recognition.face_encodings(rgb, boxes)

			for (box, encoding) in zip(boxes, encodings):
				trail_process.compare_faces_with_trial_data(inputImage_path, box, encoding, contentId, playbackTime)
		else:
			image_url_list = fetch_data_from_master_db(actors,contentId,config)
			create_encodings(contentId,image_url_list,inputImage_path,playbackTime,config)
	else:
		return

def fetch_data_from_master_db(actors,contentId,config):
	config = configparser.ConfigParser()
	config.read('config.ini')
	URI_SEPARATOR = config['MONGODB'] ['URI_SEPARATOR']
	mongo_uri = config['MONGODB'] ['MONGO_URI']
    #mongo_uri = "http://localhost:9000/actors/firstName/lastName"
	image_url_list = []
	for actor in actors:
		actor_list = []
		actor_list.extend(actor.split())
		mongo_uri_actor = mongo_uri+actor_list[0] + URI_SEPARATOR + actor_list[1]
		#print(mongo_uri_actor)
		resp = requests.get(mongo_uri_actor)
		list_images = resp.json()['images']
		name = resp.json()['name']
		image_url = resp.json()['url']
		image_url_list.append(image_url)
		#print(image_url)
		print(name)
		actor = actor.strip()
		create_images_from_byteArray(list_images, actor, contentId, config)
	return image_url_list


def create_images_from_byteArray(list_images, actor, contentId, config):
	config = configparser.ConfigParser()
	config.read('config.ini')

	PATH_SEPARATOR = config['TRIAL_DATA'] ['PATH_SEPARATOR']

	i=0
	for image_data in list_images:
        #print(config['DIR_PATHS'] ['SAMPLE_DATA_PATH'])
		folderpath = config['DIR_PATHS'] ['SAMPLE_DATA_PATH'] + str(contentId) + PATH_SEPARATOR + actor + PATH_SEPARATOR
		filename = folderpath+actor+"_"+str(i)+".png"

		if not os.path.exists(os.path.dirname(folderpath)):
			try:
				os.makedirs(os.path.dirname(folderpath))
			except OSError as exc:  # Guard against race condition
				if exc.errno != errno.EEXIST:
					raise
		if not os.path.exists(filename):
			try:
				fh = open(filename, 'wb')
				imgdata = base64.b64decode(str(image_data))
				fh.write(imgdata)
				fh.close()
			except OSError as exc:  # Guard against race condition
				if exc.errno != errno.EEXIST:
					raise

		i=i+1


def create_encodings(contentId,image_url_list,inputImage_path,playbackTime,config):

	config = configparser.ConfigParser()
	config.read('config.ini')

	PATH_SEPARATOR = config['TRIAL_DATA'] ['PATH_SEPARATOR']

    #print(config['DIR_PATHS'] ['ENCODINGS_PATH'])
	encodingsPath = config['DIR_PATHS'] ['ENCODINGS_PATH']

	encodingsfile = "encodings"+ PATH_SEPARATOR +"encodings_" + str(contentId) + ".pickle"

    ## start with comparison process
	if not os.path.exists(os.path.dirname(encodingsPath)):
		try:
			os.makedirs(os.path.dirname(encodingsPath))
			#print("create encodings Now")

    ## Fetch Actors/images result from Master DB and store it in folders..
    ## Call encode_faces.py. So, now we have encodings Ready!!

    ## os.system("encode_faces.py -i dataset -e encodingsPath -d 'CNN'")
		except OSError as exc:  # Guard against race condition
			if exc.errno != errno.EEXIST:
				raise
    
	if not os.path.exists(encodingsfile):
		try:
			picklefile = open(encodingsfile, "wb")
			picklefile.close()
            
			#print("create encodings Now")
			folderpath = "sample_images"+ PATH_SEPARATOR +"inputimage_" + str(contentId)

			encode_faces.createEncodings(folderpath, encodingsfile, 'CNN')

        ## Fetch Actors/images result from Master DB and store it in folders..
        ## Call encode_faces.py. So, now we have encodings Ready!!

        ## os.system("encode_faces.py -i dataset -e encodingsPath -d 'CNN'")
		except OSError as exc:  # Guard against race condition
			if exc.errno != errno.EEXIST:
				raise

	list_data = recognize_faces_image.recognize_faces(contentId, inputImage_path, encodingsfile, 'CNN', playbackTime, image_url_list, 'yes')
	#print(list_data)

	encodings = list_data[0]
	boxes = list_data[1]
	names = list_data[2]

	print("playbackTime:>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ")
	print(playbackTime)
	print("boxes:>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ")
	print(boxes)
	print("names: >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ")
	print(names)
	loop = 0
	for(name, box, encoding) in zip(names, boxes, encodings):
		if(name == 'Unknown'):
            #call trial process with (inputImage_path, box, encoding, contentId, playbackTime)
			trail_process.compare_faces_with_trial_data(inputImage_path, boxes[loop], encoding, contentId, playbackTime)
            #unknown_image_trail_process.compare_faces_with_trial_data(inputImage_path, boxes[loop], encoding, contentId, playbackTime)
		loop = loop + 1