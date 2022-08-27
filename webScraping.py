import re
import urllib
from urllib.request import Request, urlopen
import os


def dl_jpg(url,file_path,file_name):
	full_path = file_path + file_name + '.jpg'
	urllib.request.urlretrieve(url,full_path)

firstName=input("Enter the actor's first Name :")
lastName=input("Enter the actor's last Name :")
url="https://www.google.com/search?q="+firstName+"%20"+lastName+"&tbm=isch&tbs=isz%3Am&hl=en-GB&ved=0CAIQpwVqFwoTCLiLxfKn5OUCFQAAAAAdAAAAABAC&biw=1263&bih=578"
print(url)


headers = {}
headers['User-Agent'] = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
req = urllib.request.Request(url, headers=headers)
resp = urllib.request.urlopen(req)
respData = str(resp.read())
ff=open("C:\\Users\\vshetti\\Desktop\\POC\\"+firstName+" "+lastName+".txt",'w')
for word in respData:
	ff.write(str(word))
ff.close()

q=re.compile(r'http[s]?://[\w\d]+[.][\w\d]+[.]?[\w\d]*[.]*[//\w\d[-]*[\w\d]]*[.]jpg')
fd=open("C:\\Users\\vshetti\\Desktop\\POC\\"+firstName+" "+lastName+".txt",'r')
fu=open("C:\\Users\\vshetti\\Desktop\\POC\\downloads\\"+firstName+" "+lastName+".txt",'w')
t_list=[word for word in (fd.read()).split('"')]
count=0
for word in t_list:
	m=q.match(word)
	if m:
		print(m.group())
		count+=1
		ur=m.group()
		fu.write(ur)
		fu.write("\n")
print("Total URLs: "+str(count))
fu.close()

counter=0
fu=open("C:\\Users\\vshetti\\Desktop\\POC\\downloads\\"+firstName+" "+lastName+".txt",'r')
if not os.path.exists("C:\\Users\\vshetti\\Desktop\\POC\\downloads\\"+firstName+" "+lastName):
	os.mkdir("C:\\Users\\vshetti\\Desktop\\POC\\downloads\\"+firstName+" "+lastName)
	for url in fu.readlines():
		try:
			file_path="C:\\Users\\vshetti\\Desktop\\POC\\downloads\\"+firstName+" "+lastName+"\\"
			dl_jpg(url,file_path,firstName+"_"+str(counter))
			counter+=1
		except:
			pass
			
else:
	for url in fu.readlines():
		try:
			file_path="C:\\Users\\vshetti\\Desktop\\POC\\downloads\\"+firstName+" "+lastName+"\\"
			dl_jpg(url,file_path,firstName+"_"+str(counter))
			counter+=1
		except:
			pass