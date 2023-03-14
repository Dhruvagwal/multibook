import pyrebase
import urllib

firebaseConfig = {
  "apiKey": "AIzaSyDvoUdQOfIw0Z7He-hUufpaaq_6NH5qvmg",
  "authDomain": "onelangworld.firebaseapp.com",
  "projectId": "onelangworld",
  "storageBucket": "onelangworld.appspot.com",
  "messagingSenderId": "764040324034",
  "appId": "1:764040324034:web:17b532e6ca86312130ac5b",
  "measurementId": "G-KDNP1Y673V",
  "databaseURL": ""
}

firebase = pyrebase.initialize_app(firebaseConfig)

# Setting Up Storage
storage=firebase.storage()

def store(cloudfilename, file):
    print(cloudfilename)
    storage.child(cloudfilename).put(file)
    url =  storage.child(cloudfilename).get_url(None)
    return url
    
def read(cloudfilename):
    path=storage.child(cloudfilename).get_url(None)
    try:
        f = urllib.request.urlopen(path)
        return path
    except:
        return None

def check(url):
    try:
        f = urllib.request.urlopen(url)
        return True
    except:
        return False
    
if __name__ == '__main__':
    read("/fonts/Arial.ttf")