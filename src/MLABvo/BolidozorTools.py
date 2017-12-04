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



def estimate_dopplers(trajectory, timesteps, rec_station, trans_station, f0 = 143050000):
    # alternative algorithm
    '''
        Returns array of dopplers for given transmitter to receiver position and defined frequency and known trajectory.
    '''
    doppler = np.empty([trajectory.shape[0], 2])
    doppler_offset = 0
    t = timesteps[1] - timesteps[0]

    for i in range(trajectory.shape[0]):
        try: 
            # angle transmitter - meteor - reciever
            ba = trans_station-trajectory[i]
            bc = rec_station-trajectory[i]
            TMR = np.arccos(np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc)))

            # angle trajectory - meteor - reciever
            ba = trajectory[i+1]-trajectory[i]
            bc = rec_station-trajectory[i]
            VMR = np.arccos(np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc)))
            
            # angle trajectory - meteor - axis (of angle transmitter-meter-reciever)
            VMA = VMR-TMR/2
            
            # radial speed of meteor to axis of TMR angle (Transmitter - meteor - reciever)
            radial_speed = np.cos(VMA)*(np.linalg.norm(trajectory[i]-trajectory[i+1])/t)
            doppler_offset = (radial_speed/c)*f0
            
        except Exception as e:
            pass

        doppler[i] = np.array([timesteps[i], doppler_offset])
    return doppler