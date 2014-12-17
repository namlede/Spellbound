#Source code copied from http://stackoverflow.com/questions/2632520/what-is-the-fastest-way-to-send-100-000-http-requests-in-python#answer-2635066
from urlparse import urlparse
from threading import Thread
import httplib, sys
from Queue import Queue

def doWork():
    while True:
        url, path = q.get()
        result, url = getStatus(url)
        doSomethingWithResult(result, url, path)
        q.task_done()

def getStatus(ourl):
    try:
        url = urlparse(ourl)
        conn = httplib.HTTPSConnection(url.netloc)
        conn.request("GET", url.path)
        res = conn.getresponse()
        return res.read(), ourl
    except:
        #what to do here?
        return "error", ourl

def doSomethingWithResult(result, url, path):
    data[path] = result
    global todo
    todo-=1
def get_text(owner,repo,branch,file_path):
    global todo
    todo+=1
    q.put(("https://raw.githubusercontent.com/" + owner + "/" + repo + "/"+branch+"/" + file_path,file_path))

def init():
    for i in range(concurrent):
        t = Thread(target=doWork)
        t.daemon = True
        t.start()
def start():
    working=True
    q.join()
todo=0
working=False
data={}
concurrent=13 #For some reason bugs occur when this is larger than 13...
q = Queue(concurrent * 2)#why *2?
