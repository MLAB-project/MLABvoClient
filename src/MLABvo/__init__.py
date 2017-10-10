
import requests
import datetime
import time

class MLABvo(object):
    job_id = ""
    wait = None
    def __init__(self, arg=None, server_mvo = 'http://api.vo.astro.cz/bolidozor/', debug = False, wait = True):
        self.arg = arg
        self.debug = debug
        self.wait = wait

        self.server_mvo = server_mvo
        self.station_id = None
        self.station_name = None
        self.station_param = None
        
    def _makeRequest(self, url, arguments=None, timeout = 2):
        if self.debug: print(self.server_mvo+url, arguments)
        req =  requests.get(self.server_mvo+url, params=arguments, timeout = timeout).json()
        self.job_id = req['job_id']
        return req

    def getResult(self, job_id = None, delay = 1/4):
        if not job_id: job_id = self.job_id
        if self.debug: print("getResult",job_id, self.wait, delay)
        return retrieveData(id = job_id, wait = self.wait, delay = delay)


class retrieveData():
    state = 'PENDING'

    def  __init__(self, id, delay = 1/2, wait = True):
        self.delay = delay
        self.timeout = 2
        self.data = None
        self.result = None
        self.server_mvo = 'http://api.vo.astro.cz/bolidozor/'+'job/'+id
        if wait:
            self.run(wait = True)

    def isReady(self):
        data = requests.get(self.server_mvo, timeout = self.timeout).json()
        if data['job_state'] == 'SUCCESS':
            return True
        else:
            return False

    def run(self, wait = False):
        data = requests.get(self.server_mvo, timeout = self.timeout).json()
        self.state = data['job_state']
        
        while wait and data['job_state'] != 'SUCCESS':
            data = requests.get(self.server_mvo, timeout = self.timeout).json()
            self.state = data['job_state']
            time.sleep(self.delay)

        if data['job_state'] == 'SUCCESS':
            self.data  = data
            self.result  = data['result']
            return data
        else:
            return False

    def fetch(self):
        if self.state == 'SUCCESS':
            return self.data
        else:
            return None
