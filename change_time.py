
from PIL import Image
import piexif
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
import os


#    img = Image.open(filename)
#    if "exif" in img.info:
#                exif_dict = piexif.load(img.info["exif"])


for root, dirs, files in os.walk("./dslr_images"):
    if not files:
        continue
    prefix = os.path.basename(root)
    for f in files:
        #print os.path.join(root, f)
        exif_dict = piexif.load(os.path.join(root, f))

        td1 = timedelta(hours=1)
        td2 = timedelta(minutes=3)
        td3 = timedelta(seconds=40)
        
        # 0th.DateTime
        if piexif.ImageIFD.DateTime in exif_dict["0th"]:
            dto_date              = datetime.strptime(exif_dict['0th'][306].decode('utf-8')[O, '%Y:%m:%d %H:%M:%S')
            dto_date              = dto_date + td1 - td2
            exif_dict['0th'][306] = dto_date.strftime('%Y:%m:%d %H:%M:%S')

        # Exif.DateTimeOriginal
        if piexif.ExifIFD.DateTimeOriginal in exif_dict["Exif"]:
            dto_date_orig = datetime.strptime(exif_dict['Exif'][36867].decode("utf-8") , '%Y:%m:%d %H:%M:%S')
            dto_date_orig = dto_date_orig + td1 - td2
            exif_dict['Exif'][36867] = dto_date_orig.strftime('%Y:%m:%d %H:%M:%S')
        if piexif.ExifIFD.DateTimeOriginal in exif_dict["Exif"]:
            dto_date_digi = datetime.strptime(exif_dict['Exif'][36868].decode("utf-8") , '%Y:%m:%d %H:%M:%S')
            dto_date_digi = dto_date_digi + td1 - td2
            exif_dict['Exif'][36868] = dto_date_digi.strftime('%Y:%m:%d %H:%M:%S')

        # GPS.GPSTimeStamp  !!!!!
        if piexif.GPSIFD.GPSTimeStamp in exif_dict["GPS"]:
            gps_ts              = map(list, exif_dict['GPS'][7])         
            #gps_ts[0][0]        = gps_ts[0][0]+1
            #gps_ts[1][0]        = gps_ts[1][0]-3

            gps_ts[0][0]        = dto_date.hour
            gps_ts[1][0]        = dto_date.minute
        
            exif_dict['GPS'][7] = tuple(tuple(x) for x in gps_ts)
        

        # GPS.GPSDateStamp
        if piexif.GPSIFD.GPSDateStamp in exif_dict["GPS"]:
            exif_dict['GPS'][29] = dto_date.strftime('%Y:%m:%d')

        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, os.path.join(root, f))
        

        #print (date, dto_date_orig, dto_date_digi, gps_tsm, dto_gps_ds)
        #print "-------------------------------------------"
        #for ifd in ("0th", "Exif", "GPS", "1st"):
        #    for tag in exif_dict[ifd]:
        #        print(ifd, tag, piexif.TAGS[ifd][tag]["name"], exif_dict[ifd][tag])
        #        #os.rename(os.path.join(root, f), os.path.join(root, "{} ID {}".format(prefix, f)))



