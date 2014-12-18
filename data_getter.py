#Source code copied from http://stackoverflow.com/questions/2632520/what-is-the-fastest-way-to-send-100-000-http-requests-in-python#answer-2635066
from urlparse import urlparse
from threading import Thread
from os import makedirs
import os.path
import httplib, sys
from Queue import Queue

def doWork():
    while True:
        url, path = q.get()
        result, url = getStatus(url)
        doSomethingWithResult(result, url, path)
        q.task_done()

def getStatus(ourl):
    url = urlparse(ourl)
    file_path=".cache"+url.path
    if os.path.exists(file_path):
        cached_file=open(file_path,"r")
        text=cached_file.read()
        cached_file.close()
        return text,ourl
    else:
        conn = httplib.HTTPSConnection(url.netloc)
        conn.request("GET", url.path)
        res = conn.getresponse()
        dir_name = os.path.dirname(file_path)
        #From: http://stackoverflow.com/questions/8344315/create-path-and-filename-from-string-in-python
        # create directory if it does not exist
        if not os.path.exists(dir_name):
            try:
                makedirs(dir_name)
            except:
                pass #async problems
        to_cache_file=open(file_path,"w")
        to_cache_file.write(res.read())
        to_cache_file.close()
        return res.read(), ourl

def doSomethingWithResult(result, url, path):
    data[path] = result
def get_text(owner,repo,branch,file_path):
    q.put(("https://raw.githubusercontent.com/" + owner + "/" + repo + "/"+branch+"/" + file_path+secret,file_path))

def init(info):
    if info:
        secret="?"+info[1:]
    for i in range(concurrent):
        t = Thread(target=doWork)
        t.daemon = True
        t.start()
def start():
    q.join()
data={}
secret=""
concurrent=4 #For some reason bugs occur when this is larger than 13...
q = Queue(concurrent * 2)#why *2?
