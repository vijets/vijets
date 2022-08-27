# USAGE
# python recognize_faces_image.py --encodings encodings.pickle --image examples/example_01.png 

# import the necessary packages
import face_recognition
import argparse
import pickle
import cv2
import post_data

def recognize_faces(contentId, inputImage_path, encodingsfile, detection_method, playbackTime, image_url_list, post_data_to_db):

	#image_url and playbacktime
	image_url_list = image_url_list
	playbackTime = playbackTime
	#print(image_url_list)
	#print(playbackTime)

	# load the known faces and embeddings
	#print("[INFO] loading encodings...")
	data = pickle.loads(open(encodingsfile, "rb").read())

	# load the input image and convert it from BGR to RGB
	image = cv2.imread(inputImage_path)
	(h, w) = image.shape[:2]
	rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

	# detect the (x, y)-coordinates of the bounding boxes corresponding
	# to each face in the input image, then compute the facial embeddings
	# for each face
	#print("[INFO] recognizing faces...")
	boxes = face_recognition.face_locations(rgb,
		model=detection_method)
	loop = 0
	boxes_updated = boxes
	for box in boxes:
		if not(is_traceable_face(h, w, box)):
			boxes_updated.remove(box)
	
	print("original box: ")
	print(boxes)
	print("box updated: ")
	print(boxes_updated)
	
	
	encodings = face_recognition.face_encodings(rgb, boxes_updated)
	# initialize the list of names for each face detected
	names = []
	votes = []
	counts = {}
	# loop over the facial embeddings
	for encoding in encodings:
		#print("inside encoding in encodings loop")
		# attempt to match each face in the input image to our known
		# encodings
		matches = face_recognition.compare_faces(data["encodings"],
			encoding)
		name = "Unknown"
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
				name = data["names"][i]
				counts[name] = counts.get(name, 0) + 1
			#for name in counts:
			#	if (counts[name]>1):
			#		thresholdcounts[name] = counts[name]

			#for i in counts:
				#print("name: ",name," votes: ",counts[name])
			# determine the recognized face with the largest number of
			# votes (note: in the event of an unlikely tie Python will
			# select first entry in the dictionary)
			name = max(counts, key=counts.get)
		
		# update the list of names
		#print(name)
		names.append(name)
		if (name == "Unknown"):
			votes.append(1)
		else:
			votes.append(counts[name])
		print("identified:",name )

	# loop over the recognized faces
	loop = 0
	known_boxes = []
	known_names = []
	for ((top, right, bottom, left), name, vote) in zip(boxes_updated, names, votes):
		#print(boxes[0])
		if name != "Unknown":
			# Logic need to be implemented to identify percantage of votes here..... based on the sample input strength....
			sample_image_count_of_actor = find_image_count(name, data)
			print("sample_image_count_of_actor: "+str(sample_image_count_of_actor))
			print("vote: "+str(vote))
			vote_percantage = vote / sample_image_count_of_actor
			print("voting percantage is : "+str(vote_percantage))
			if (vote_percantage >= 0.4):
				print("Voting percantage is greater than 0.25 for the artist: "+name)
			#if (vote > 1):
				print("name: "+name)
				print("votes: "+str(vote))
				known_boxes.append(boxes_updated[loop])
				known_names.append(names[loop])
		loop = loop + 1
	#print(known_boxes)
	#print(known_names)
	#print(image_url_list)
	
	if (post_data_to_db == 'yes'):
		if(len(known_names) != 0):
			post_data.updatemetadatatodb(contentId, playbackTime, known_names, image_url_list, known_boxes)
			#print("After posting json data")
		#else:
			#print("No Actors identified in this frame.")

	return [encodings, boxes_updated, names, counts]
	
def find_image_count(name, data):
	
	names_array = data["names"]
	_size = len(names_array)
	image_count = 0
	
	for i in range(_size):
		if(name == names_array[i]):
			image_count = image_count + 1
	
	return image_count
	
def is_traceable_face(height, width, box):
	threshold = 0.3
	top = box[0]
	right = box[1]
	bottom = box[2]
	left = box[3]
	
	frame_resolution = height * width
	face_resolution = (bottom - top) * (right - left)
	
	face_area_on_screen = (face_resolution/frame_resolution) * 100
	print("frame_resolution : ")
	print(frame_resolution)
	print("face_resolution : ")
	print(face_resolution)
	print("face_area_on_screen : ")
	print(face_area_on_screen)
	
	if(face_area_on_screen >= threshold):
		return True
	else:
		return False