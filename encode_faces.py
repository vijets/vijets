# USAGE
# python encode_faces.py --dataset dataset --encodings encodings.pickle

# import the necessary packages
from imutils import paths
import face_recognition
import argparse
import pickle
import cv2
import os

def createEncodings(dataset, encodingsfile, detection_method):

	# grab the paths to the input images in our dataset
	#print("[INFO] quantifying faces...")
	imagePaths = list(paths.list_images(dataset))

	# initialize the list of known encodings and known names
	knownEncodings = []
	knownNames = []

	# loop over the image paths
	for (i, imagePath) in enumerate(imagePaths):
		# extract the person name from the image path
		#print("[INFO] processing image {}/{}".format(i + 1,
		#	len(imagePaths)))
		name = imagePath.split(os.path.sep)[-2]
		#print(name)
		# load the input image and convert it from RGB (OpenCV ordering)
		# to dlib ordering (RGB)
		image = cv2.imread(imagePath)
		#print("After reading image")
		rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
		#print("After reading rgb")
		# detect the (x, y)-coordinates of the bounding boxes
		# corresponding to each face in the input image
		boxes = face_recognition.face_locations(rgb,
			model=detection_method)

		#print("After creating boxes_"+ str(boxes))
		# compute the facial embedding for the face
		encodings = face_recognition.face_encodings(rgb, boxes)

		# loop over the encodings
		for encoding in encodings:
			# add each encoding + name to our set of known names and
			# encodings
			knownEncodings.append(encoding)
			knownNames.append(name)

	# dump the facial encodings + names to disk
	#print("[INFO] serializing encodings...")
	data = {"encodings": knownEncodings, "names": knownNames}
	f = open(encodingsfile, "wb+")
	f.write(pickle.dumps(data))
	f.close()


def append_encodings(imagePath, ENCODINGS_FILE, name, detection_method):
	image = cv2.imread(imagePath)
	rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
	boxes = face_recognition.face_locations(rgb,
			model=detection_method)
	encodings = face_recognition.face_encodings(rgb, boxes)
	
	if (len(encodings) != 0):
		#now fetch the encodings and append new encoding to the dictionary along with name
		pickle_in = open(ENCODINGS_FILE,"rb")
		encodings_dict = pickle.load(pickle_in)
		encodings_list = encodings_dict["encodings"]
		names_list = encodings_dict["names"]
		pickle_in.close()
		
		pickle_out = open(ENCODINGS_FILE,"wb+")
		encodings_list.append(encodings[0])
		names_list.append(name)
		data = {"encodings": encodings_list, "names": names_list}
		pickle_out.write(pickle.dumps(data))
	
	
	