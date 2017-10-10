import MLABvo
import requests
import datetime
import json
from astropy.io import fits

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as md
from matplotlib import dates
import sys
import math


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


    def getMeteor(self, station = None, date_from = None, date_to = datetime.datetime.now(), min_duration = None):
        #TODO: pokud je stanice text, tak ji vyhledat v db (pomoci getStation) a nastavit (self.setStation())
        
        if station and not type(station) == int: 
            raise Exception("argument 'station' must be integer or None (not %s). It presents 'station_id'" %(type(station)))
        
        if station == None:
            station = self.station_id
        
        snapshots = self._makeRequest('getMeteor/', {'station_id':station, 'date_from':date_from, 'date_to': date_to, 'min_duration':min_duration})
        return self.getResult(snapshots['job_id'])
    
    def getMultibolid(self, id = None):
        
        multibolid = self._makeRequest('getMultibolid/', {'id':id})
        return self.getResult(multibolid['job_id'])


        try:
            pass
        except Exception as e:
            raise
        else:
            pass
        finally:
            pass




def samp2time(sample):
    return sample/2*1/96000

def time2samp(time):
    return time*2*96000

def smooth(y, box_pts):
    box = np.ones(box_pts)/box_pts
    y_smooth = np.convolve(y, box, mode='full')
    return y_smooth


def getMeteorAround(station, time, distance = datetime.timedelta(minutes=600), debug = False):
    try:
        b = Bolidozor(debug = debug)
        print(station, b.setStation(station))

        meteors = b.getMeteor(date_from=time-distance, date_to=time+distance, min_duration=1).result
        #if len(meteors) > 0:
            #for met in meteors:
            #    print(met['url_file_raw'], met['duration'], met['obstime'])
    
        return meteors
    except Exception as e:
        print('getMeteorAround', e)
        return False


def timeCalibration(raw_file, station=None, sigma = 15, debug = True, browse_around = True):
    calibration_data = {}
    calibration_data['samp_correction'] = 0
    # Stahnout a otevrit RAW fits meteoru
    hdulist = fits.open(raw_file, cache=True)
    met_data = np.abs(np.ravel(hdulist[0].data))
    met_smooth = smooth(met_data, 25)
    clip_val = np.std(met_data)*sigma
    
    #file_length = hdulist[0].header['NAXIS2']*hdulist[0].header['CDELT2']/1000.0
    file_length = samp2time(hdulist[0].header['NAXIS2']*2)
    DATE_OBS = datetime.datetime.strptime(hdulist[0].header['DATE-OBS'], "%Y-%m-%dT%H:%M:%S" )
    DATE = datetime.datetime.strptime(hdulist[0].header['DATE'], "%Y-%m-%dT%H:%M:%S" )
    calibration_data['sys_file_beg'] = DATE-datetime.timedelta(seconds=file_length)
    calibration_data['sys_file_end'] = DATE
    
    if debug: plt.axhline(y=clip_val, color='red')
    max_val = np.max(met_data)
    time_firstGPS = None
    ten_sec = []
        
    # Tato cast hleda v datech GPS znacky
    # Kdyz je najde, zapise je do seznamu `ten_sec`
    # Prvni GPS znacku to ulozi jako float do `time_firstGPS`
    
    for i, point in enumerate(met_smooth):
        if point > clip_val:
            if not time_firstGPS:
                 time_firstGPS = samp2time(i)
                 if debug: 
                    plt.axvline(x=time2samp(time_firstGPS), color='red', lw=2)
                    plt.axvline(x=time2samp(time_firstGPS)+time2samp(10), color='green', lw=2)
            ten_sec.append(samp2time(i))
    
    # Ohodnotit kvalitu dat,
        #  100 - Velmi dobre - jasna GPS znacka,
        #  50  - Znacka neni - najdeme ji v jinem souboru a zarovname podle vzorku zvukovky
        #  0  - Data jsou nekvalitni, nelze je pouzivat
    
    if time_firstGPS:
        calibration_data['quality'] = 100
        calibration_data['method'] = 'GPS'
        gps = (DATE-datetime.timedelta(seconds=file_length-time_firstGPS)).timestamp()
        correction = seconds=round(gps/10.0)*10-gps
    elif clip_val > 0.9:
        calibration_data['quality'] = 0
        calibration_data['method'] = 'Null'
        correction = 0
    else:
        calibration_data['quality'] = 50
        calibration_data['method'] = 'Around GPS'
        correction = 0
        
        # Kdyz je kvalita 50 (znacka neni v rozsahu zaznamu),
        #  tak se pokusi sehnat seznam okolnich meteoru,
        #  ve kterych najde GPS znacky
    
        if browse_around and station:
            time_offset = []
            if debug: print("hledam alternativni zdroj presneho casu")
            around = getMeteorAround(station, datetime.datetime.strptime(hdulist[0].header['DATE'], "%Y-%m-%dT%H:%M:%S" ))
            if around:
                print("Okolnich souboru:", len(around))
                for meteor in around:
                    meteor_data = timeCalibration(meteor['url_file_raw'], debug=False, browse_around = False)
                    if meteor_data['quality'] == 100:

                        time_offset.append([
                            meteor_data['CRVAL2'],
                            meteor_data['cor_file_beg'].replace(tzinfo=datetime.timezone.utc).timestamp(),
                            meteor_data['samp_correction'],
                            #meteor_data['CRVAL2']-meteor_data['cor_file_beg'].replace(tzinfo=datetime.timezone.utc).timestamp()
                                            ])
                        print("+", end='')
                    else:
                        print("-", end='')
                        
                ## plt.plot(time_offset)
                #plt.show()
                #for ar in time_offset:
                #    print("%f %f %f" %(ar[0], ar[1], ar[2]))
                mean = np.mean(np.array(time_offset)[:,2])
                print("mean: %f, std: %f" %(mean, np.std(np.array(time_offset)[:,2])))
                calibration_data['samp_correction'] = mean
            else:
                print("## Nelze najit zadne dalsi meteory v okoli")
                calibration_data['method'] = 'Null'
                calibration_data['quality'] = 25
            
                    
    if not time_firstGPS: time_firstGPS = 0
    correction = datetime.timedelta(seconds=correction)
    
    
    calibration_data['CRVAL2'] = hdulist[0].header['CRVAL2']/1000.0
    calibration_data['DATE-OBS'] = DATE_OBS
    
    calibration_data['sys_1st_GPS'] = DATE-datetime.timedelta(seconds=file_length-time_firstGPS)
    calibration_data['sys_error'] = DATE-datetime.timedelta(seconds=file_length-time_firstGPS)
    
    calibration_data['cor_file_beg'] = DATE-datetime.timedelta(seconds=file_length)+correction
    calibration_data['cor_file_end'] = DATE+correction
    calibration_data['cor_1st_GPS'] = DATE-datetime.timedelta(seconds=file_length-time_firstGPS)+correction
    
    calibration_data['sys_correction'] = correction
    if calibration_data['samp_correction'] == 0:
        calibration_data['samp_correction'] = calibration_data['CRVAL2']-calibration_data['cor_file_beg'].replace(tzinfo=datetime.timezone.utc).timestamp()
    else:
        calibration_data['cor_file_beg'] = datetime.datetime.utcfromtimestamp(calibration_data['CRVAL2'])-datetime.timedelta(seconds=calibration_data['samp_correction'])
        calibration_data['cor_file_end'] = datetime.datetime.utcfromtimestamp(calibration_data['CRVAL2'])-datetime.timedelta(seconds=calibration_data['samp_correction']-file_length)
        calibration_data['cor_1st_GPS'] = datetime.datetime.utcfromtimestamp(calibration_data['CRVAL2'])-datetime.timedelta(seconds=calibration_data['samp_correction'])
    
    if debug:
        #DATE_OBS = datetime.datetime.strptime(hdulist[0].header['DATE-OBS'], "%Y-%m-%dT%H:%M:%S" )
        print("Zpracovavam soubor:", raw_file)
        print('delka zaznamu          :', file_length, "s")
        print('cas prvni. vzorku s GPS:', time_firstGPS, "s")
        print('cas 1. GPS a konec     :', file_length - time_firstGPS, "s")
        print('SysCas ukladani souboru:', calibration_data['sys_file_end'], "s")
        print('SysCas zacatku souboru :', calibration_data['sys_file_beg'])
        print('SysCas 1. GPS znacky   :', calibration_data['sys_1st_GPS'])
        print('Korekce systemoveho cas:', calibration_data['sys_correction'])
        print('Korekce casu zvukovky  :', calibration_data['samp_correction'])
        print('CorCas ukladani souboru:', calibration_data['cor_file_end'], "s")
        print('CorCas zacatku souboru :', calibration_data['cor_file_beg'])
        print('CorCas 1. GPS znacky   :', calibration_data['cor_1st_GPS'])
        print('Kvalita souboru        :', calibration_data['quality'])
        print('Pocet vzorku s gps znac:', len(ten_sec))
        plt.plot(met_data, lw=0.5)
        plt.plot(met_smooth)
        plt.show()
    return calibration_data

def waterfall(signal, sample_rate=None, bins = 4096 ):
    waterfall = waterfallize(signal, bins)
    waterfall[np.isneginf(waterfall)] = np.nan
    wmin, wmax = np.nanmin(waterfall), np.nanmax(waterfall)
    return waterfall


def waterfallize(signal, bins):
    window = 0.5 * (1.0 - np.cos((2 * math.pi * np.arange(bins)) / bins))
    segment = int(bins / 2)
    nsegments = int(len(signal) / int(segment))
    m = np.repeat(np.reshape(signal[0:int(segment * nsegments)], (int(nsegments), int(segment))), 2, axis=0)
    t = np.reshape(m[1:int(len(m) - 1)], (int(nsegments - 1), int(bins)))
    img = np.multiply(t, window)
    wf = np.log(np.abs(np.fft.fft(img)))
    return np.concatenate((wf[:, int(bins / 2):int(bins)], wf[:, 0:int(bins / 2)]), axis=1)