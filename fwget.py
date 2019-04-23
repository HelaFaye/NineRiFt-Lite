import os
from os import path
import requests
from kivy.utils import platform
import hashlib


class FWGet():
    def __init__(self, cache):
        self.cachePath = cache
        self.repoURL = "http://null"
        self.dirname = "null"
        if not os.path.exists(self.cachePath):
            os.makedirs(self.cachePath)
            print("Created NineRiFt cache directory")

    def setRepo(self, repo):
        self.repoURL = repo

    def md5Checksum(self, filePath, url):
        m = hashlib.md5()
        if url==None:
            with open(filePath, 'rb') as fh:
                m = hashlib.md5()
                while True:
                    data = fh.read(8192)
                    if not data:
                        break
                    m.update(data)
                return m.hexdigest()
        else:
            r = requests.get(url)
            for data in r.iter_content(8192):
                 m.update(data)
            return m.hexdigest()

    def getFile(self, FWtype, version):
        if (self.repoURL == "http://null" or self.dirname == "null"):
            print("You need to load a valid repo first.")
            return(False)
        noInternet = False
        if not os.path.exists(self.cachePath + "/" + self.dirname + "/"):
            os.makedirs(self.cachePath + "/" + self.dirname + "/")
            print("Created repo cache directory")
        try:
            r = requests.head(self.repoURL)
            if (r.status_code != 200):
                noInternet = True
                print("Failed to connect to the repo, using local files if available (Server response not 200)")
        except requests.ConnectionError:
            print("Failed to connect to the repo, using local files if available (requests.ConnectionError)")
            noInternet = True
        filename = FWtype.upper() + version + ".bin.enc"
        completePath = self.cachePath + "/" + self.dirname + "/" + filename
        isFilePresent = os.path.isfile(completePath)
        if noInternet == False:
            response = requests.get(self.repoURL + FWtype.lower() + "/" + filename + ".md5")
            with open(completePath + ".md5", 'wb') as f:
                f.write(response.content)
            checksum = response.text
            if isFilePresent:
                match = self.md5Checksum(completePath, None) == checksum
            else:
                match = False
        else:
            if isFilePresent:
                with open(completePath + ".md5", "r") as md5cached:
                    checksum = md5cached.read()
                    match = self.md5Checksum(completePath, None) == checksum
        if (isFilePresent and match):
            print(filename + ' was cached; moving on')
            return(True, completePath)
        else:
            url = self.repoURL + FWtype.lower() + "/" + filename
            try:
                r = requests.head(url)
                if (r.status_code == 404):
                    print("Failed to fetch " + filename + " (Error 404 file not found)")
                    return(False, completePath)
                print('Beginning file download; writing to ' + completePath)
                url = self.repoURL + FWtype.lower() + "/" + filename
                print("URL: " + url)
                r = requests.get(url)
                with open(completePath, 'wb') as f:
                    f.write(r.content)
                if (r.status_code == 200):
                    print(filename + " downloaded successfully.")
                    return(True, completePath)
                else:
                    print("Server couldn't respond to download request. Local files aren't available. Aborting.")
                    return(False, completePath)
            except requests.ConnectionError:
                print("Connection error. Local files aren't available. Aborting.")
                return(False, completePath)

    def loadRepo(self, jsonURL):
        d = ''
        noInternet = False
        hashedName = hashlib.md5(jsonURL).hexdigest()
        try:
            r = requests.head(jsonURL)
            if (r.status_code != 200):
                noInternet = True
                print("Failed to fetch JSON! Will use cached if available. (Server response not 200)")
        except requests.ConnectionError:
            print("Failed to fetch JSON! Will use cached if available. (requests.ConnectionError)")
            noInternet = True
        if noInternet == False:
            try:
                r = requests.get(jsonURL)
                with open(self.cachePath + hashedName + ".json", 'wb') as f:
                    f.write(r.content)
                with open(self.cachePath + hashedName + ".json") as f:
                    d = eval(f.read())
                    print("Fetched repo JSON.")
            except requests.ConnectionError:
                print("Failed to grab JSON! (requests.ConnectionError)")
                return(False)

        elif os.path.isfile(self.cachePath + hashedName + ".json"):
            with open(self.cachePath + hashedName + ".json") as f:
                d = eval(f.read())
            print("Fetched cached repo JSON.")
        else:
            print("Couldn't download file and couldn't load from cache. Aborting.")
            return(False)
        self.dirname = str(d["repo"]["infos"]["dirname"])
        self.repoURL = str(d["repo"]["infos"]["files_URL"])
        name = str(d["repo"]["infos"]["name"])
        DRV = d["repo"]["files"]["DRV"]
        BMS = d["repo"]["files"]["BMS"]
        BLE = d["repo"]["files"]["BLE"]
        print("Loaded the repo \"" + name+ "\" hosted at " +  self.repoURL + ". DRV:"
         + str(DRV) + " BMS:" + str(BMS) + " BLE:" + str(BLE))
        return(True, self.dirname, self.repoURL, name, DRV, BMS, BLE)

    def Gimme(self, firm, ver):
        self.getFile(firm,ver)
