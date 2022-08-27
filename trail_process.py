import face_recognition
import argparse
import pickle
import cv2
import os
import io
from PIL import Image
import numpy as np
import recognize_faces_image
import encode_faces
import shutil
import configparser
import base64
import requests
import detect_faces

def compare_faces_with_trial_data(inputImage_path, face_locations, encoding, contentId, playbackTime):
    
	#print("inputImage_path:")
	#print(inputImage_path)
	#print("face_locations:")
	#print(face_locations)
	#print("contentId:")
	#print(contentId)
	#print("playbackTime:")
	#print(playbackTime)
	
	config = configparser.ConfigParser()
	config.read('config.ini')

	DETECTION_MODEL = config['TRIAL_DATA'] ['DETECTION_MODEL']
	UNKNOWN_IMAGE_PATH = config['TRIAL_DATA'] ['UNKNOWN_IMAGE_PATH']
	TRIAL_ENCODINGS_PATH = config['TRIAL_DATA'] ['TRIAL_ENCODINGS_PATH']
	TRIAL_ENCODINGS_FILE_NAME = config['TRIAL_DATA'] ['TRIAL_ENCODINGS_FILE_NAME']
	FIRST_UNKNOWN_FOLDER_NAME = config['TRIAL_DATA'] ['FIRST_UNKNOWN_FOLDER_NAME']
	PATH_SEPARATOR = config['TRIAL_DATA'] ['PATH_SEPARATOR']
	UNKNOWN_IMAGE_FIRST_PART = config['TRIAL_DATA'] ['UNKNOWN_IMAGE_FIRST_PART']
	UNKNOWN_IMAGE_MIDDLE_PART = config['TRIAL_DATA'] ['UNKNOWN_IMAGE_MIDDLE_PART']
	UNKNOWN_IMAGE_LAST_PART = config['DIR_PATHS'] ['IMAGE_FORMAT']

	temp_dir_path = config['TRIAL_DATA'] ['TEMP_DIR_PATH']
	tmp_file_name = config['TRIAL_DATA'] ['TEMP_FILE_NAME']
	
	TRIAL_ENCODINGS_FILE = TRIAL_ENCODINGS_PATH + TRIAL_ENCODINGS_FILE_NAME


	confidence = config['DNN_CONFIGS'] ['CONFIDENCE']
	caffefile = config['DNN_CONFIGS'] ['CAFE']
	protoxtfile = config['DNN_CONFIGS'] ['PROTOXT']
	encode_dir_exists = os.path.exists(os.path.dirname(TRIAL_ENCODINGS_PATH))
	encode_file_exists = os.path.exists(TRIAL_ENCODINGS_FILE)

	if not  encode_file_exists :
        
		crop_and_save_image(UNKNOWN_IMAGE_PATH + FIRST_UNKNOWN_FOLDER_NAME, inputImage_path, face_locations, contentId, playbackTime)
		#call method to save the image.
		if not encode_dir_exists :
			try:
				os.makedirs(os.path.dirname(TRIAL_ENCODINGS_PATH))
				#print("create encodings Now")
    ## Fetch Actors/images result from Master DB and store it in folders..
    ## Call encode_faces.py. So, now we have encodings Ready!!
    ## os.system("encode_faces.py -i dataset -e encodingsPath -d 'CNN'")
			except OSError as exc:  # Guard against race condition
				if exc.errno != errno.EEXIST:
					raise
			#print(TRIAL_ENCODINGS_FILE)
		if not encode_file_exists :
			try:
				picklefile = open(TRIAL_ENCODINGS_FILE, "wb")
				picklefile.close()
				#print("create encodings Now")
                #folderpath = "sample\\trail"
				encode_faces.createEncodings(UNKNOWN_IMAGE_PATH, TRIAL_ENCODINGS_FILE, DETECTION_MODEL)
			except OSError as exc:  # Guard against race condition
				if exc.errno != errno.EEXIST:
					raise

    # recognize face
	if encode_file_exists :
        #create a Temporary image to compare with the existing encodings
		temp_img_path = temp_dir_path + tmp_file_name
		tmp_dir_exists = os.path.exists(os.path.dirname(temp_dir_path))
		if not tmp_dir_exists :
			try:
				os.makedirs(os.path.dirname(temp_dir_path))
			except OSError as exc:  # Guard against race condition
				if exc.errno != errno.EEXIST:
					raise
		image = cv2.imread(inputImage_path)
		(height, width) = image.shape[:2]

		y1 = face_locations[0] - 40 if face_locations[0] - 40 > 0 else face_locations[0]
		y2 = face_locations[2] + 40 if face_locations[2] + 40 < height else face_locations[2]
		x1 = face_locations[3] - 40 if face_locations[3] - 40 > 0 else face_locations[3]
		x2 = face_locations[1] + 40 if face_locations[1] + 40 < width else face_locations[1]
		crop = image[y1:y2, x1:x2]
		cv2.imwrite(temp_img_path, crop)
		if (detect_faces.image_detections(inputImage_path, protoxtfile, caffefile, confidence) == True):
			#compare face  get directory name 

			dist_dict = {}
			#name_found = 'Unknown'

			#if (len(names) != 0):
			name_found = recognize_face(encoding, TRIAL_ENCODINGS_FILE)
			#name_found = names[0]
			print(name_found)
			if "EMPTY" != name_found :
				if 'Unknown' == name_found :
				#create new directory
				#print(len(next(os.walk(UNKNOWN_IMAGE_PATH))[1]))
					total_unknown_dirs = (len(next(os.walk(UNKNOWN_IMAGE_PATH))[1]))
					DIR_PATH = UNKNOWN_IMAGE_PATH+'UK'+str(total_unknown_dirs+1)+PATH_SEPARATOR
					dir_exists = os.path.exists(os.path.dirname(DIR_PATH))
					if not (dir_exists):
						try:
							os.makedirs(os.path.dirname(DIR_PATH))
						except OSError as exc:  # Guard against race condition
							if exc.errno != errno.EEXIST:
								raise
					image_path = DIR_PATH + UNKNOWN_IMAGE_FIRST_PART + str(contentId)+ UNKNOWN_IMAGE_MIDDLE_PART + '1' + UNKNOWN_IMAGE_LAST_PART
					unknown_folder_name = 'UK'+str(total_unknown_dirs+1)
					shutil.copy2(temp_img_path, image_path)
					encode_faces.append_encodings(image_path, TRIAL_ENCODINGS_FILE, unknown_folder_name, DETECTION_MODEL)
					post_data_to_grouping_db(image_path, contentId, playbackTime, unknown_folder_name)
					print("Above data is for the image in the path: "+image_path)
					#encode_faces.createEncodings(UNKNOWN_IMAGE_PATH, TRIAL_ENCODINGS_FILE, 'HOG')

				else :
					#save image in direc_name of trial data.
					save_in_folder = UNKNOWN_IMAGE_PATH + name_found + PATH_SEPARATOR
					no_of_images = len([name for name in os.listdir(save_in_folder) if os.path.isfile(os.path.join(save_in_folder, name))])
					#copy image from temp path to save_in_folder path
					image_path = save_in_folder + UNKNOWN_IMAGE_FIRST_PART + str(contentId) + UNKNOWN_IMAGE_MIDDLE_PART + str(no_of_images+1) + UNKNOWN_IMAGE_LAST_PART
					shutil.copy2(temp_img_path, image_path)
					encode_faces.append_encodings(image_path, TRIAL_ENCODINGS_FILE, name_found, DETECTION_MODEL)
					#Post Data to database which keeps unknown actors...
					post_data_to_grouping_db(image_path, contentId, playbackTime, name_found)
					print("Above data is for the image in the path: "+image_path)
					#encode_faces.createEncodings(UNKNOWN_IMAGE_PATH, TRIAL_ENCODINGS_FILE, 'HOG')


def crop_and_save_image(image_dir_path, inputImage_path, face_locations, contentId, playbackTime):


	config = configparser.ConfigParser()
	config.read('config.ini')

	UNKNOWN_IMAGE_FIRST_PART = config['TRIAL_DATA'] ['UNKNOWN_IMAGE_FIRST_PART']
	UNKNOWN_IMAGE_MIDDLE_PART = config['TRIAL_DATA'] ['UNKNOWN_IMAGE_MIDDLE_PART']
	UNKNOWN_IMAGE_LAST_PART = config['DIR_PATHS'] ['IMAGE_FORMAT']

	image_dir_exists = os.path.exists(os.path.dirname(image_dir_path))
	if not image_dir_exists :
		try:
			os.makedirs(os.path.dirname(image_dir_path))
		except OSError as exc:  # Guard against race condition
			if exc.errno != errno.EEXIST:
				raise

	imagePath = inputImage_path
	image = cv2.imread(imagePath)
	(height, width) = image.shape[:2]
	DIR = image_dir_path
	#print (len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))]))
	no_of_images = len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])

	y1 = face_locations[0] - 40 if face_locations[0] - 40 > 0 else face_locations[0]
	y2 = face_locations[2] + 40 if face_locations[2] + 40 < height else face_locations[2]
	x1 = face_locations[3] - 40 if face_locations[3] - 40 > 0 else face_locations[3]
	x2 = face_locations[1] + 40 if face_locations[1] + 40 < width else face_locations[1]
	crop = image[y1:y2, x1:x2]
	cv2.imwrite(image_dir_path + UNKNOWN_IMAGE_FIRST_PART + str(contentId) + UNKNOWN_IMAGE_MIDDLE_PART + str(no_of_images+1) + UNKNOWN_IMAGE_LAST_PART ,crop)

def post_data_to_grouping_db(image_path, contentId, playbackTime, name):
    #convert image to base64 String...
	config = configparser.ConfigParser()
	config.read('config.ini')

	ENCODING = config['TRIAL_DATA'] ['ENCODING_TYPE']
	POST_ACTOR_DATA_URI = config['TRIAL_DATA'] ['POST_ACTOR_DATA_URI']
	#ENCODING = 'utf-8'
	#print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>             image_path: ")
	#print(image_path)
	with open(image_path, "rb") as image_file:
		encoded_bytes = base64.b64encode(image_file.read())
		#print("encoded_bytes is >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
		#print(encoded_bytes)
		base64_string = encoded_bytes.decode(ENCODING)
		image_file.close()
		actors_detail = {"contentId":contentId, "actorName":name, "imageBase64Str":base64_string, "playbackTime":playbackTime}
		headers = {"Content-type":"application/json"}
		#POST_ACTOR_DATA_URI = "http://10.197.24.3:8089/unknownactor/"
		actor_response = requests.post(url=POST_ACTOR_DATA_URI,json=actors_detail,headers=headers)
		#assert actor_response.status_code == 201
		
def recognize_face(encoding, TRIAL_ENCODINGS_FILE):

	data = pickle.loads(open(TRIAL_ENCODINGS_FILE, "rb").read())
	
	matches = face_recognition.compare_faces(data["encodings"],
		encoding)
	name = "Unknown"
	counts = {}
	vote_percantage_dict = {}
	
	config = configparser.ConfigParser()
	config.read('config.ini')

	VOTE_PERCENTAGE_THRESHOLD = config['TRIAL_DATA'] ['VOTE_PERCENTAGE_THRESHOLD']
	
	# check to see if we have found a match
	if True in matches:
		counts.clear()
		# find the indexes of all matched faces then initialize a
		# dictionary to count the total number of times each face
		# was matched
		matchedIdxs = [i for (i, b) in enumerate(matches) if b]
		#counts = {}
		#thresholdcounts = {}
		# loop over the matched indexes and maintain a count for
		# each recognized face face
		for i in matchedIdxs:
			actorname = data["names"][i]
			counts[actorname] = counts.get(actorname, 0) + 1
		
		for key in counts:
			print(key)
			#Findout the percantage of votes for every key/name identified 
			vote_1 = counts[key]
			image_count_1 = find_image_count(key, data)
			vote_percantage_1 = vote_1 / image_count_1
			vote_percantage_dict[key] = vote_percantage_1
		
		print("vote_percantage_dict: ")
		print(vote_percantage_dict)
		name_acc_to_percantage = max(vote_percantage_dict, key=vote_percantage_dict.get)
		print("name_acc_to_percantage: ")
		print(name_acc_to_percantage)
		
		# determine the recognized face with the largest number of
		# votes (note: in the event of an unlikely tie Python will
		# select first entry in the dictionary)
		
		
		
		#name = max(counts, key=counts.get)
		#image_count = find_image_count(name, data)
		#print("sample_image_count_of_actor: "+str(image_count))
		#vote = counts[name]
		#print("vote: "+str(vote))
		#vote_percantage = vote / image_count
		#print("voting percantage is : "+str(vote_percantage))
		vote_percantage = vote_percantage_dict[name_acc_to_percantage]
		if (vote_percantage >= float(VOTE_PERCENTAGE_THRESHOLD)):
			name = name_acc_to_percantage
			print("Voting percantage is greater than 0.25 for the artist:>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> "+name)
		else:
			print("Voting percantage is lesser than 0.25 for the artist:<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< "+name)
			name = "Unknown"
	print("name found iniial process is: "+name)
	return name	
	
def find_image_count(name, data):
	
	names_array = data["names"]
	_size = len(names_array)
	image_count = 0
	
	for i in range(_size):
		if(name == names_array[i]):
			image_count = image_count + 1
	
	return image_count