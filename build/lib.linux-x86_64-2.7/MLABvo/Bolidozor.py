import MLABvo
import requests
import datetime
import json

class Bolidozor(MLABvo.MLABvo):
    def __init__(self, *args, **kwargs):
        super(Bolidozor, self).__init__(*args, **kwargs)

    def getStation(self, id = None, name = None, all=False, get_data = True):
        if id and name:
            raise Exception("Can not be set 'id' and 'name' parametr together.")
        elif all:
            stations = self._makeRequest('getStation/', {'all':all})
        else:
            stations = self._makeRequest('getStation/', {'id':id, 'name':name})
        self.last_job = stations['job_id']
        
        return self.getResult(stations['job_id'])
    
    def setStation(self, station):
        if type(station) is list:
            station = station[0]
        
        if type(station) is dict:
            self.station_id = station['id']
            self.station_name = station['namesimple']
            self.station_param = station

        elif type(station) is int:
            out = self.getStation(id = station)
            self.station_id = out.data['result'][0]['id']
            self.station_name = out.data['result'][0]['namesimple']
            self.station_param = out.data['result'][0]

        elif type(station) is str:
            out = self.getStation(name = station)
            self.station_id = out.data['result'][0]['id']
            self.station_name = out.data['result'][0]['namesimple']
            self.station_param = out.data['result'][0]

        elif station == None:
            self.station_id = None
            self.station_name = None
            self.station_param = None

        return True


    def delStation(self):
        self.setStation(None)
    


    def getSnapshot(self, station = None, date_from = None, date_to = datetime.datetime.now()):
        #TODO: pokud je stanice text, tak ji vyhledat v db (pomoci getStation) a nastavit (self.setStation())
        
        if station and not type(station) == int: 
            raise Exception("argument 'station' must be integer or None (not %s). It presents 'station_id'" %(type(station)))
        
        if station == None:
            station = self.station_id
        
        snapshots = self._makeRequest('getSnapshot/', {'station_id':station, 'date_from':date_from, 'date_to': date_to})
        return self.getResult(snapshots['job_id'])


    def getMeteor(self, station = None, date_from = None, date_to = datetime.datetime.now()):
        #TODO: pokud je stanice text, tak ji vyhledat v db (pomoci getStation) a nastavit (self.setStation())
        
        if station and not type(station) == int: 
            raise Exception("argument 'station' must be integer or None (not %s). It presents 'station_id'" %(type(station)))
        
        if station == None:
            station = self.station_id
        
        snapshots = self._makeRequest('getMeteor/', {'station_id':station, 'date_from':date_from, 'date_to': date_to})
        return self.getResult(snapshots['job_id'])
    
    def getMultibolid(self, id = None):
        
        multibolid = self._makeRequest('getMultibolid/', {'id':id})
        return self.getResult(multibolid['job_id'])