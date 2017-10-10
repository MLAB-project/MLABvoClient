from MLABvo.Bolidozor import Bolidozor
import datetime
import MLABvo
import json
import time


def main():
    b = Bolidozor(wait = True)
    #stations = b.getStation()
    #for station in stations.data['result']:
    #    print station['id'], station['namesimple'], "\t\t", station['name']

    #b.setStation(stations.data['result'][3])
    b.setStation('OBSUPICE-R6')

    #b.delStation()
 
    snapshots = b.getSnapshot(date_from = datetime.datetime(2017, 9, 24), date_to = datetime.datetime(2017, 9, 25))
 

    while not snapshots.isReady():
        print "none", snapshots.state
        time.sleep(1)

    print type(snapshots.data)
    print len(snapshots.data['result'])
    for snap in snapshots.data['result']:
        print snap['id_observer'], snap['filename']




if __name__ == '__main__':
    main()