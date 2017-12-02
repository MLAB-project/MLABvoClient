from MLABvo.Bolidozor import Bolidozor
from MLABvo.Bolidozor import timeCalibration
from MLABvo.Bolidozor import waterfall
import datetime
from astropy.io import fits
import json
import numpy as np

import matplotlib as mpl
mpl.use('Agg')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as md
from matplotlib import dates
#oimport mpltools
import sys



def proceed(multibolid_id):
    bz = Bolidozor()
    bolids = bz.getMultibolid(id=multibolid_id)
    print('Pocet detekci ve skupine je',len(bolids.result))

    for i, bolid in enumerate(bolids.result):
        try:
            print(i,"==================================")
            print("snapshot:", bolid['url_file_js9'])
            bolids.result[i]['time_calib']=timeCalibration(bolid['url_file_raw'], bolid['station_name'], sigma=10, debug = False)
        except Exception as e:
            print("for bolids.result:", e)

    time_offset = {}
    selected = list(range(0, len(bolids.result)))

    for i, bolid in enumerate(bolids.result):
        if bolid['time_calib']['quality'] < 50:
            selected.remove(i)

    count = len(selected)
    gps_calib = True
    minimal_time = None
    maximal_time = None

    for i, s in enumerate(selected):
        try:
            bolid = bolids.result[selected[i]]
            met_data = np.abs(np.ravel(fits.open(bolid['url_file_raw'])[0].data))

            T_offset = 10*time_offset.get(selected[i], 0)

            if gps_calib:
                min_date = bolid['time_calib']['cor_file_beg'].replace(tzinfo=datetime.timezone.utc).timestamp()+T_offset
                max_date = bolid['time_calib']['cor_file_end'].replace(tzinfo=datetime.timezone.utc).timestamp()+T_offset
            else:
                min_date = bolid['time_calib']['sys_file_beg'].replace(tzinfo=datetime.timezone.utc).timestamp()+T_offset
                max_date = bolid['time_calib']['sys_file_end'].replace(tzinfo=datetime.timezone.utc).timestamp()+T_offset
            array = np.arange(min_date, max_date, (max_date-min_date)/(len(met_data)))

            if not minimal_time: minimal_time = min_date
            if not maximal_time: maximal_time = max_date
            if min_date < minimal_time: minimal_time = min_date
            if max_date > maximal_time: maximal_time = max_date

        except Exception as e:
            print(e)

    fig, axis = plt.subplots(1, count, sharex=True, sharey=True, figsize=(20, 10))

    #fig.tight_layout()
    fig.suptitle("Multibolid %s (%s)" %(datetime.datetime.utcfromtimestamp(minimal_time).date(), multibolid_id))
    plt.set_cmap('hot')

    for i, ax in enumerate(axis):
        bolid = bolids.result[selected[i]]
        hdu = fits.open(bolid['url_file_raw'])[0]
        flat_data = np.ravel(hdu.data)
        
        T_offset = datetime.timedelta(seconds = 10*time_offset.get(selected[i], 0))
        d1 = bolid['time_calib']['cor_file_beg']+T_offset
        fds1 = dates.date2num(d1) # converted
        d2 = d1 + datetime.timedelta(seconds=hdu.header['NAXIS2']/96000.0)
        fds2 = dates.date2num(d2)
        
        arr = waterfall(flat_data[0::2] + 1j * flat_data[1::2], None, bins = 4096*3)
        ax.imshow(arr,  interpolation='nearest', aspect='auto',  extent=[-48000, 48000, fds2, fds1])
        ax.grid(True)
        
        ax.set_xlim(26000,27000)
        ax.yaxis_date()
        date_format = md.DateFormatter('%H:%M:%S')
        ax.yaxis.set_major_formatter(date_format)
        fig.autofmt_xdate()
        ax.set_ylim( datetime.datetime.utcfromtimestamp(minimal_time), datetime.datetime.utcfromtimestamp(maximal_time))
        
        ax.set_title(bolid['namesimple'])
    fig.subplots_adjust(wspace=0.04, left = 0.03, right=0.98, bottom=0.03, top=0.93)
    plt.savefig('multibolid_%s.png' %(multibolid_id), dpi=150, bbox_inches='tight')



def main():
    bz = Bolidozor()
    if len(sys.argv) > 1: proceed(sys.argv[1])
    else:
        last = 0
        events = []
        groups = (bz.getMultibolids(date_from=datetime.datetime.utcnow()-datetime.timedelta(days=5)))
        for i, group in enumerate(groups.result):
            if not group['match_id'] in events:
                events += [group['match_id']]
        print(events)
        print(type(events))
        for  i, group in enumerate(reversed(events)):
            try:
                print("############################# event,",group, i+1, '/', len(events))
                print(group)
                proceed(group)
            except Exception as e:
                print(e)

if __name__ == '__main__':
    main()
