# USAGE
# python detect_faces.py --image rooster.jpg --prototxt deploy.prototxt.txt --model res10_300x300_ssd_iter_140000.caffemodel

# import the necessary packages
import numpy as np
import argparse
import cv2

# construct the argument parse and parse the arguments
#ap = argparse.ArgumentParser()
#ap.add_argument("-i", "--image", required=True,
#	help="path to input image")
#ap.add_argument("-p", "--prototxt", required=True,
#	help="path to Caffe 'deploy' prototxt file")
#ap.add_argument("-m", "--model", required=True,
#	help="path to Caffe pre-trained model")
#ap.add_argument("-c", "--confidence", type=float, default=0.5,
#	help="minimum probability to filter weak detections")
#args = vars(ap.parse_args())

# load our serialized model from disk
def image_detections(inputImage_path, protoxtfile, caffefile, confidence_threshold):
	#print("[INFO] loading model...")
	net = cv2.dnn.readNetFromCaffe(protoxtfile, caffefile)

	# load the input image and construct an input blob for the image
	# by resizing to a fixed 300x300 pixels and then normalizing it
	image = cv2.imread(inputImage_path)
	(h, w) = image.shape[:2]
	#print("height: "+str(h))
	#print("width: "+str(w))
	#blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 1.0,
	blob = cv2.dnn.blobFromImage(image, 1.0,
		(300, 300), (104.0, 177.0, 123.0))

	# pass the blob through the network and obtain the detections and
	# predictions
	#print("[INFO] computing object detections...")
	net.setInput(blob)
	detections = net.forward()
	boxes = []
	# loop over the detections
	for i in range(0, detections.shape[2]):
		# extract the confidence (i.e., probability) associated with the
		# prediction
		confidence = detections[0, 0, i, 2]

		# filter out weak detections by ensuring the `confidence` is
		# greater than the minimum confidence
		if confidence > float(confidence_threshold):
			# compute the (x, y)-coordinates of the bounding box for the
			# object
			box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
			(startX, startY, endX, endY) = box.astype("int")
			boxes.append((startX, startY, endX, endY))
			#print(box)
			#print(startX, startY, endX, endY)

	if (len(boxes) !=0):
		return True
	else:
		return False