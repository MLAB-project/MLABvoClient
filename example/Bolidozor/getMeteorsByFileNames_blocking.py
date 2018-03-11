%load_ext autoreload
%autoreload 2

from MLABvo.Bolidozor import Bolidozor
import time

b = Bolidozor()

filelist = [
        '20180311084621220_NACHODSKO-R5',
        '20180311084619744_OBSUPICE-R6',
        '20160315120635630_VALMEZ-R1'
    ]

data = b.getMeteorByFiles(filelist)

for a in data.data['result']:
    print(a['url_file_raw'])
