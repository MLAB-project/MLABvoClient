from MLABvo.Bolidozor import Bolidozor
from MLABvo.Bolidozor import timeCalibration
from MLABvo.Bolidozor import waterfall
import datetime
from astropy.io import fits
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as md
from matplotlib import dates
import mpltools

multibolid_id = 1573599
bz = Bolidozor()
bolids = bz.getMultibolid(id=multibolid_id)
print('Pocet detekci ve skupine je',len(bolids.result))

for i, bolid in enumerate(bolids.result):
    try:
        print(i,"==================================")
        print("snapshot:", bolid['url_file_js9'])
        bolids.result[i]['time_calib']=timeCalibration(bolid['url_file_raw'], bolid['station_name'], debug = False)
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


fig, axis = plt.subplots(1, count, sharex=True, sharey=True, figsize=(25, 15))

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
    d2 = d1 + datetime.timedelta(seconds=hdu.header['NAXIS2']/49000.0/2)
    fds2 = dates.date2num(d2)
    
    arr = waterfall(flat_data[0::2] + 1j * flat_data[1::2], 49000, bins = 4096*4)
    ax.imshow(arr,  interpolation='none', aspect='auto',  extent=[-24000, 24000, fds2, fds1])
    ax.grid(True)
    
    ax.set_xlim(13000,13500)
    ax.yaxis_date()
    date_format = md.DateFormatter('%H:%M:%S')
    ax.yaxis.set_major_formatter(date_format)
    fig.autofmt_xdate()
    ax.set_ylim( datetime.datetime.utcfromtimestamp(minimal_time), datetime.datetime.utcfromtimestamp(maximal_time))
    
    ax.set_title(bolid['namesimple'])
plt.savefig('output.png', dpi=300)