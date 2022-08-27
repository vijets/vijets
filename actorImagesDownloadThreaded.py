import webbrowser
import time
import os
import cv2
import face_recognition
import base64
from imutils import paths
import requests
import configparser
from google_images_download import google_images_download
from PIL import Image
from flask import Flask, jsonify,request
import shutil
import threading
#from imdb import IMDb
#from imdb import Person

global actor_id
app= Flask(__name__)	
config = configparser.ConfigParser()
config.read('config.ini')
images_base_folder_path = config['DOWNLOAD_IMAGES']['DOWNLOAD_IMAGES_PATH']
No_of_images_to_be_dld = 2
response = google_images_download.googleimagesdownload()
image_type="ActiOn"
middleName=" "
@app.route('/downloadimages/<firstName>/<lastName>/<contentID>', methods=['GET'])
def downloadimages(firstName, lastName, contentID):
    actorName = firstName+middleName+lastName
    actors_detail = {"firstname":firstName, "middlename":middleName,"lastname":lastName}
    headers = {"Content-type":"application/json"}
    GET_ACTOR_DATA_URI = "http://10.197.7.198:8089/getSampleCount/"+firstName+"/"+lastName
    actor_response = requests.get(url=GET_ACTOR_DATA_URI,json=actors_detail,headers=headers)
    data=actor_response.json()
    print("Image count-->"+str(data['samplecount']))
    if((data['samplecount'])== 0):
    # keywords is the search query 
	# limit is the number of images to be downloaded
	# output_directory is the output folder for images downloaded		

        try:
            t= threading.Thread(target=download_images_filter_insert_to_DB, args=(actorName,contentID,))
            t.start()
            print("Starting thread.. total count="+str(threading.activeCount()))
            print("List of threads: "+str(threading.enumerate()))
			
	    #Collecting actors profile picture & biography from IMDB
        #actorBiography(actorName)

        # Handling File NotFound Error     
        except FileNotFoundError:  
                                   
            try: 
                t= threading.Thread(target=download_images_filter_insert_to_DB, args=(actorName,contentID,))
                t.start()
                print("Starting thread.. total count="+str(threading.activeCount()))
                print("List of threads: "+str(threading.enumerate()))
				
		#Collecting actors profile picture & biography from IMDB
		#actorBiography(actorName)

            except: 
                pass
        return "400"
    else:
        print("Actor data already available for : "+actorName+". Please check in the Sample Database" )
        print("Number of images available -->" + str(data['samplecount']))
        return "200"    
		

def download_images_filter_insert_to_DB(actorName,contentID):
    i=0
    arguments = {"keywords": actorName,"limit":No_of_images_to_be_dld,"output_directory":images_base_folder_path} 
    response.download(arguments)
    folder_path = config['DOWNLOAD_IMAGES']['DOWNLOAD_IMAGES_PATH']+actorName

    #deleting the corrupted images
    for filename in os.listdir(folder_path):
        try :
            with Image.open(folder_path + "/" + filename) as im:
                print('Image ok & readable')
        except :
            print(folder_path + "/" + filename)
            os.remove(folder_path + "/" + filename)

    #renaming the downloaded files to actor name
    for filename in os.listdir(folder_path):
        dst =actorName + str(i) + ".jpg"
        src=folder_path + "/"+ filename
        dst =folder_path + "/" + dst 
        try:
            os.rename(src, dst) 
            i+= 1
        except:
            pass

			
    #detect multiple faces in the downloaded images & delete the ones which have 2 or more faces.
    imagePaths = list(paths.list_images(folder_path))
    for (i, imagePath) in enumerate(imagePaths):
        print("Imagepath-->"+imagePath)
        if(imagePath!=""):
            # extract the person name from the image path
            print("[INFO] processing image {}/{}".format(i + 1,len(imagePaths)))
            # load the input image and convert it from RGB (OpenCV ordering)
            # to dlib ordering (RGB)
            image = cv2.imread(imagePath)
            print("After reading image")
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            print("After reading rgb")
            # detect the (x, y)-coordinates of the bounding boxes
            # corresponding to each face in the input image
            boxes = face_recognition.face_locations(rgb,model='cnn')
            print(boxes)
            if(len(boxes)>1):
                print("Deleting --> " + imagePath)
                os.remove(imagePath)
        else:
            print("No images left to process")
        
		
    imagePaths = list(paths.list_images(images_base_folder_path+actorName))
    ENCODING = 'utf-8'
    firstName=actorName.split()[0]
    lastName= actorName.split()[1]
    print("contentID-->"+str(contentID))
    for (j, imagePath) in enumerate(imagePaths):
        with open(imagePath, "rb") as image_file:
            encoded_bytes = base64.b64encode(image_file.read())
            base64_string = encoded_bytes.decode(ENCODING)
            image_file.close()

            #Push downloaded images to sample DB
            actors_detail = {"firstname":firstName, "middlename":middleName,"lastname":lastName,"imagesBase64Str":base64_string, "verified":0}
            headers = {"Content-type":"application/json"}
            POST_ACTOR_DATA_URI = "http://10.197.7.198:8089/insertActorsImages/" 
            sample_db_actor_response = requests.post(url=POST_ACTOR_DATA_URI,json=actors_detail,headers=headers)
            print("Sample DB ingestion status: "+str(sample_db_actor_response))

            #Push images to temp DB for verifying the images. 
            actors_detail = {"contentId":contentID, "firstName":firstName, "middleName":middleName,"lastName":lastName,"verified":0}
            headers = {"Content-type":"application/json"}
            POST_ACTOR_DATA_URI = "http://10.197.7.198:8089/insertSampleActor/"
            temp_db_actor_response = requests.post(url=POST_ACTOR_DATA_URI,json=actors_detail,headers=headers)
            print("temp DB ingestion  status: "+str(temp_db_actor_response))

    shutil.rmtree(images_base_folder_path+actorName)
        
		
def actorBiography(actorName): 
    ia = IMDb()
    folder_path = config['DOWNLOAD_IMAGES']['DOWNLOAD_IMAGES_PATH']+actorName
    #getting actor's IMDb ID
    people = ia.search_person(actorName)
    for person in people:
	    if(person['name']==actorName):
		    actor_id = person.personID
    print("Actor's IMDb ID is --> " +str(actor_id))

    #getting actor's profile page in IMDb
    url = "https://www.imdb.com/name/nm"+actor_id+"/?ref_=fn_al_nm_1"
    print("Actor's IMDB profile URL-->"+url)


    #getting actor's IMDb profile picture
    fu=urllib.request.urlopen(url)
    ff = open(config['DOWNLOAD_IMAGES']['IMDB_DUMP_TEXT_FILE_PATH'],"w")
    for line in fu.readlines():
	    ff.write(str(line))
    ff.close()
    fo = open(config['DOWNLOAD_IMAGES']['IMDB_DUMP_TEXT_FILE_PATH'],"r")
    for word in fo:
	    temp_list = word.split()
	    break
    for word in temp_list:
        if(re.search(r"[a-zA-Z0-9.*]*.jpg",word)):
            actor_image_url = word[6:-7]
            print("Actor's IMDb profile picture URL --> " +actor_image_url)
            urllib.request.urlretrieve(actor_image_url,folder_path)
            break
		
    #getting actor's biography
    person = ia.get_person(actor_id)
    print("Actor's Biography --> ")
    actors_bio = str(person['biography'])
    print(actors_bio)

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5005, debug=True)
 
	

	
