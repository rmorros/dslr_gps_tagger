"""
Print Exif data 

Usage:
  add_gps_data.py <imagesDir> 
  add_gps_data.py -h | --help
Options:
"""

from docopt import docopt
from PIL import Image
import piexif
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
import os


if __name__ == '__main__':
    # read arguments
    args = docopt(__doc__)
    imadir   = args['<imagesDir>']

    ref_lst = []

    for root, dirs, files in os.walk(imadir):
        if not files:
            continue
        prefix = os.path.basename(root)
        for f in sorted(files):
            #print os.path.join(root, f)
            exif_dict = piexif.load(os.path.join(root, f))


            for ifd in ("0th", "Exif", "GPS", "1st"):
                for tag in exif_dict[ifd]:
                    print(ifd, tag, piexif.TAGS[ifd][tag]["name"], exif_dict[ifd][tag])



