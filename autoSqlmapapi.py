# -*-coding:utf-8 -*-
"""
启动sqlmapapi.py:python sqlmapapi.py -s
"""
import requests
import time,re,os
import json,simplejson
import threading,sys
import Queue
from optparse import OptionParser,OptionError

TreadNum=20 #并发线程数

class AutoSqli(object):

    #使用sqlmapapi的方法进行与sqlmapapi建立的server进行交互


    def __init__(self, server='', target='',data = '',referer = '',cookie = ''):
        super(AutoSqli, self).__init__()
        self.server = server
        if self.server[-1] != '/':
            self.server = self.server + '/'
        self.target = target
        self.taskid = ''
        self.engineid = ''
        self.status = ''
        self.data = data
        self.referer = referer
        self.cookie = cookie
        self.start_time = time.time()

    def task_new(self):
        self.taskid = json.loads(
            requests.get(self.server + 'task/new').text)['taskid']
        #print 'Created new task: ' + self.taskid
        if len(self.taskid) > 0:
            return True
        return False

    def task_delete(self):
        json_kill=requests.get(self.server + 'task/' + self.taskid + '/delete').text
        # if json.loads(requests.get(self.server + 'task/' + self.taskid + '/delete').text)['success']:
        #     #print '[%s] Deleted task' % (self.taskid)
        #     return True
        # return False

    def scan_start(self):
        headers = {'Content-Type': 'application/json'}
        #print "starting to scan "+ self.target +".................."
        payload = {'url': self.target}
        url = self.server + 'scan/' + self.taskid + '/start'
        #print url
        t = json.loads(
            requests.post(url, data=json.dumps(payload), headers=headers).text)
        #print t
        self.engineid = t['engineid']
        if len(str(self.engineid)) > 0 and t['success']:
            #print 'Started scan'
            return True
        return False

    def scan_status(self):
        self.status = json.loads(
            requests.get(self.server + 'scan/' + self.taskid + '/status').text)['status']
        if self.status == 'running':
            return 'running'
        elif self.status == 'terminated':
            return 'terminated'
        else:
            return 'error'

    def scan_data(self):
        self.data = json.loads(
            requests.get(self.server + 'scan/' + self.taskid + '/data').text)['data']
        if len(self.data) == 0:
            print (self.target+' normal')
        else:
            print (self.target+' injection')
            date=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
            f=open('sqlmapapi_result/injection.txt','a')
            rs = "================================================\n"
            rs += date+"\n"
            rs += self.target+"\n"
            rs += "Response:\n"+simplejson.dumps(self.data)+'\n'
            rs +="==============================================\n"
            f.write(rs)

    def option_set(self):
        headers = {'Content-Type': 'application/json'}
        option = options
        url = self.server + 'option/' + self.taskid + '/set'
        t = json.loads(
            requests.post(url, data=json.dumps(option), headers=headers).text)
        #print t

    def scan_stop(self):
        json_stop=requests.get(self.server + 'scan/' + self.taskid + '/stop').text
        # json.loads(
        #     requests.get(self.server + 'scan/' + self.taskid + '/stop').text)['success']

    def scan_kill(self):
        json_kill=requests.get(self.server + 'scan/' + self.taskid + '/kill').text
        # json.loads(
        #     requests.get(self.server + 'scan/' + self.taskid + '/kill').text)['success']

    def run(self):
        if not self.task_new():
            return False
        self.option_set()
        if not self.scan_start():
            return False
        while True:
            if self.scan_status() == 'running':
                time.sleep(10)
            elif self.scan_status() == 'terminated':
                break
            else:
                break
            #print time.time() - self.start_time
            if time.time() - self.start_time > opts.timeout:
                print (self.target+' timeout')
                error = True
                self.scan_stop()
                self.scan_kill()
                break
        self.scan_data()
        self.task_delete()
        #print time.time() - self.start_time

class myThread(threading.Thread):
    def __init__(self,q,thread_id):
        threading.Thread.__init__(self)
        self.q=q
        self.thread_id=thread_id
    def run(self):
        while not self.q.empty():
            #print "threading "+str(self.thread_id)+" is running"
            objects=self.q.get()
            result=objects.run()


        
if __name__ == '__main__':
    urls=[]
    options={"options": {
                    "randomAgent": True,
                    "tech":"BUT",
                    "batch":True
                    }
                 }
    p=OptionParser()
    p.add_option('-l','--level',default=1,dest='level',help="Level of tests to perform (1-5, default 1)")
    p.add_option('-r','--risk',default=1,dest='risk',help="Risk of tests to perform (1-3, default 1)")
    p.add_option('-t','--timeout',default=600,dest='timeout',help="Seconds to wait before timeout connection")

    opts,args=p.parse_args()

    options["options"]['level']=opts.level
    options["options"]['risk']=opts.risk
    

    with open("get_url.txt") as f:
        urls=f.readlines()
    
    urls=[re.sub(r'\s+$','',url) for url in urls]

    workQueue=Queue.Queue()
    for tar in urls:
        s = AutoSqli('http://127.0.0.1:8775', tar)
        workQueue.put(s)
    threads = []
    nloops = range(TreadNum)   #threads Num

    for i in nloops:
        t = myThread(workQueue,i)
        t.start()
        threads.append(t)

    for i in nloops:
        threads[i].join()
    
    print ("The test is completed,View the results under the directory sqlmapapi_result")
