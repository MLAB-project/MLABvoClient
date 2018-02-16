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

import sympy as sp
from scipy import constants


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



def doppler_equation(freq = 143050000, delta = True):
    M1_x = sp.Symbol('M1_x')
    M1_y = sp.Symbol('M1_y')
    M1_z = sp.Symbol('M1_z')

    M2_x = sp.Symbol('M2_x')
    M2_y = sp.Symbol('M2_y')
    M2_z = sp.Symbol('M2_z')

    VEL = sp.Symbol('Velocity')

    TX_x = sp.Symbol('TX_x')
    TX_y = sp.Symbol('TX_y')
    TX_z = sp.Symbol('TX_z')

    RX_x = sp.Symbol('RX_x')
    RX_y = sp.Symbol('RX_y')
    RX_z = sp.Symbol('RX_z')

    t = sp.Symbol('time')

    TX = sp.Matrix([TX_x, TX_y, TX_z])  # poloha vysilace
    RX = sp.Matrix([RX_x, RX_y, RX_z])  # poloha stanice
    M1 = sp.Matrix([M1_x, M1_y, M1_z])  # prvni souradnice trajektorie
    M2 = sp.Matrix([M2_x, M2_y, M2_z])  # druha souradnice trajektorie
    MV = (M2-M1).normalized()        # normalizovany vektor trajoktie

    # poloha meteoru v case 'time'
    MT = M1 + MV*VEL*t

    #B_pn = (RX-TX).cross((RX-MT)) # bistatic plane normal

    Vmt = (TX-MT).normalized()
    Vmr = (RX-MT).normalized()
    Vba = Vmt+Vmr

    l1, l2 = sp.Line3D(MT, TX), sp.Line3D(MT, RX)
    bistatic_angle = l1.angle_between(l2)
    
    #l1, l2 = sp.Line3D(MT, MT+Vba), sp.Line3D(MT, MT+MV)
    l1, l2 = sp.Line3D(MT, RX), sp.Line3D(MT, MT+MV)
    angle = l1.angle_between(l2)

    #doppler = (int(not delta)+(sp.acos(angle)*VEL)/(constants.c))*freq
    doppler = freq * (sp.cos(angle - bistatic_angle/2)*VEL) / constants.c

    return doppler

def waterfall(signal, sample_rate=None, bins = 4096 ):
    waterfall = waterfallize(signal, bins)
    waterfall[np.isneginf(waterfall)] = np.nan
    #wmin, wmax = np.nanmin(waterfall), np.nanmax(waterfall)
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