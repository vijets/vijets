import os,hashlib
import sys
from os.path import join


def apply_hashlib(FileName):
    hasher = hashlib.md5()
    with open(str(FileName), 'rb') as afile:
        buf = afile.read()
        hasher.update(buf)
    #print(hasher.hexdigest())

    name, ext = os.path.splitext(FileName)
    new_file_name = name+'__'+ hasher.hexdigest() +  ext

    os.rename(FileName, new_file_name)
    print(name+'__'+ hasher.hexdigest() +  ext)


print(sys.argv)
working_dir = ""

if sys.argv[1]:
    working_dir = sys.argv[1]
else:
    working_dir = os.getcwd()

print(working_dir)

#print(os.getcwd())
#for (dirname, dirs, files) in os.walk(r'C:\md5_to_files'):
for (dirname, dirs, files) in os.walk(working_dir):
   for filename in files:
       if filename.endswith('.pds') or filename.endswith('.dpf') or filename.endswith('.bin'):
           thefile = os.path.join(dirname,filename)
           #print(os.path.getsize(thefile), thefile)
           apply_hashlib(thefile)

