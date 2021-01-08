"""
Add GPS data to untagged pictures based on the tags from similar pictures from the mobile phone 

Usage:
  add_gps_data.py <taggedImagesDir> <unTaggedImagesDir>  [--distThreshold=<dt>] [--timeThreshold=<tt>] [--timeOffset=<to>] [--timeZoneCorr=<tz>]
  add_gps_data.py -h | --help
Options:
  --distThreshold=<dt>        Distance in meters [default: 1500]
  --timeThreshold=<tt>        Time in seconds [default: 500]
  --timeOffset=<to>           Offset to ADD to untagged images time to compensate clock errors [default: 0]
  --timeZoneCorr=<tz>         Time zone correction (in hours). -1 in winter, -2 in summer [default: -1]
"""

from docopt import docopt
from PIL import Image
import piexif
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
#import geopy.distance 
#import LatLon3
from LatLon3 import LatLon
from fractions import Fraction
from decimal import Decimal
import sys
import os
from print_exif import print_exif_dict

    
def _convert_to_degrees(value):
    """
    Helper function to convert the GPS coordinates stored in the EXIF to degrees in float format
    :param value:
    :type value: exifread.utils.Ratio
    :rtype: float
    """
    d = float(value[0][0]) / float(value[0][1])
    m = float(value[1][0]) / float(value[1][1])
    s = float(value[2][0]) / float(value[2][1])
    
    return d + (m / 60.0) + (s / 3600.0)
                    

def get_exif_location(exif_dict):
    """
    Returns the latitude and longitude, if available, from the provided exif_data (obtained through piexif.load())
    """
    lat = None
    lon = None

    gps_latiref           = []
    gps_lati              = []
    gps_longref           = []
    gps_long              = []
    gps_altiref           = []
    gps_alti              = []
    
    if piexif.GPSIFD.GPSLatitudeRef in exif_dict["GPS"]:
        gps_latiref           = exif_dict['GPS'][1]
    if piexif.GPSIFD.GPSLatitude in exif_dict["GPS"]:
        gps_lati              = list(map(list, exif_dict['GPS'][2]))
    if piexif.GPSIFD.GPSLongitudeRef in exif_dict["GPS"]:
        gps_longref           = exif_dict['GPS'][3]
    if piexif.GPSIFD.GPSLongitude in exif_dict["GPS"]:
        gps_long              = list(map(list, exif_dict['GPS'][4]))
    if piexif.GPSIFD.GPSAltitudeRef in exif_dict["GPS"]:
        gps_altiref           = exif_dict['GPS'][5]
    if piexif.GPSIFD.GPSAltitude in exif_dict["GPS"]:
        gps_alti              = list(exif_dict['GPS'][6])

    if gps_lati and gps_latiref and gps_long and gps_longref:
        lat = _convert_to_degrees(gps_lati)
        if gps_latiref != b'N':
            lat = 0 - lat
            
        lon = _convert_to_degrees(gps_long)
        if gps_longref != b'E':
            lon = 0 - lon
    else: 
        return []
            
    return [[lat, lon], gps_latiref, gps_lati, gps_longref, gps_long, gps_altiref, gps_alti]

#---------------------------------------

if __name__ == '__main__':
    # read arguments
    args = docopt(__doc__)
    tagimadir   = args['<taggedImagesDir>']
    untagimadir = args['<unTaggedImagesDir>']

    offset      = int(args['--timeOffset'])
    tzc         = int(args['--timeZoneCorr'])

    offset_time = timedelta(seconds = offset)  # Can be negative
    tzc_time    = timedelta(hours = tzc)
    
    dist_threshold = float(args['--distThreshold'])
    td_threshold   = timedelta(seconds = float(args['--timeThreshold']))

    ref_lst = []

    for root, dirs, files in os.walk(tagimadir):
        if not files:
            continue
        prefix = os.path.basename(root)
        for f in sorted(files):
            print (os.path.join(root, f))
            exif_dict = piexif.load(os.path.join(root, f))

            if piexif.ExifIFD.DateTimeOriginal in exif_dict["Exif"]:
                dto_date_orig = datetime.strptime(exif_dict['Exif'][36867].decode('utf-8'), '%Y:%m:%d %H:%M:%S')
            else:
                print ('No EXIF time!')
                continue

            # Read 0th.DateTime
            #if piexif.ImageIFD.DateTime in exif_dict["0th"]:
            #    dto_date              = datetime.strptime(exif_dict['0th'][306], '%Y:%m:%d %H:%M:%S')

            gps_info = get_exif_location(exif_dict)

            if not gps_info:
                print ('No EXIF GPS data!')
                continue
                
            ref_lst.append([dto_date_orig, os.path.join(root, f), gps_info])

    
    # Sort by date        
    ref_lst.sort(key=lambda x: x[0]) 

    #print(ref_lst)
    #print ('\n\n')

    for root, dirs, files in os.walk(untagimadir):
        if not files:
            continue
        prefix = os.path.basename(root)
        for f in sorted(files):
            print (os.path.join(root, f))
            exif_dict = piexif.load(os.path.join(root, f))

            # Read 0th.DateTime
            if piexif.ExifIFD.DateTimeOriginal in exif_dict["Exif"]:
                dto_date_orig = datetime.strptime(exif_dict['Exif'][36867].decode('utf-8'), '%Y:%m:%d %H:%M:%S') + tzc_time + offset_time
                
                exif_dict['Exif'][36867] = bytes(dto_date_orig.strftime('%Y:%m:%d %H:%M:%S'), 'utf-8') # DateTimeOriginal
                exif_dict['Exif'][36868] = bytes(dto_date_orig.strftime('%Y:%m:%d %H:%M:%S'), 'utf-8') # DateTimeDigitized
                exif_dict['Exif'][36880] = b'+01:00'  # OffsetTime
                exif_dict['Exif'][36881] = b'+01:00'  # OffsetTimeOriginal
                exif_dict['Exif'][36882] = b'+01:00'  # OffsetTimeDigitized
            else:
                print ('No target EXIF time!')
                sys.exit()

                            
            # Find the position of dto_date between two elements of ref_lst (sorted list)
            count = 0
            while count < len(ref_lst) and dto_date_orig > ref_lst[count][0]:
                count = count + 1
                
            #print (count, dto_date_orig, ref_lst[count-1][0], ref_lst[count][0])
            gps_tag = LatLon.LatLon(0.0, 0.0)
            
            if count > 0 and count < len(ref_lst):  
                #dist      = geopy.distance.vicently(ref_lst[count-1][2][0], ref_lst[count][2][0]).km

                # LatLon objects with the references coordinates
                prev = LatLon.LatLon(LatLon.Latitude(ref_lst[count-1][2][0][0]), LatLon.Longitude(ref_lst[count-1][2][0][1]))
                next = LatLon.LatLon(LatLon.Latitude(ref_lst[count][2][0][0]),   LatLon.Longitude(ref_lst[count][2][0][1]))
                
                # Altitudes of previous and next references
                prev_alt_ref = ref_lst[count-1][2][5]
                prev_alt     = ref_lst[count-1][2][6]
                next_alt_ref = ref_lst[count][2][5]
                next_alt     = ref_lst[count][2][6]
                    
                # Compute distance and heading using LatLon3 package
                dist = prev.distance(next, ellipse = 'sphere')
                initial_heading = prev.heading_initial(next, ellipse = 'sphere')
                
                # Compute temporal differences between current date and references
                td_prev  = dto_date_orig - ref_lst[count-1][0]
                td_next  = ref_lst[count][0] - dto_date_orig
                td_tot   = ref_lst[count][0] - ref_lst[count-1][0]
                factor   = td_prev.total_seconds() / td_tot.total_seconds()
                
                if dist < dist_threshold:
                    # GPS coords
                    gps_tag  = prev.offset(initial_heading, dist * factor, ellipse = 'sphere')
                    # Altitude
                    if prev_alt_ref != next_alt_ref:
                        new_alt_ref = 0
                        new_alt     = [0,0]
                    else:
                        new_alt_ref = prev_alt_ref
                        pprev_alt = prev_alt[0] / prev_alt[1]
                        nnext_alt = next_alt[0] / next_alt[1]
                        
                        ttd_prev = td_prev.total_seconds()
                        ttd_next = td_next.total_seconds()
                        
                        nnew_alt  = (pprev_alt * ttd_prev + nnext_alt * ttd_next) / (ttd_prev + ttd_next)
                        new_alt = [0,0]
                        new_alt[0] = int(round(nnew_alt*100))
                        new_alt[1] = 100
                        
                    print (os.path.join(root, f), 'using prev and next points: {} - {}'.format(ref_lst[count-1][1], ref_lst[count][1]))

                elif td_prev < td_threshold:
                    # GPS coords
                    gps_tag     = prev
                    # Altitude
                    new_alt_ref = prev_alt_ref
                    new_alt     = prev_alt

                    print (os.path.join(root, f), 'using prev point: {}'.format(ref_lst[count-1][1]))
                    
                elif td_next < td_threshold:
                    # GPS coords
                    gps_tag = next
                    # Altitude
                    new_alt_ref = next_alt_ref
                    new_alt     = next_alt

                    print (os.path.join(root, f), 'using next point: {}'.format(ref_lst[count][1]))

                else:
                    print (os.path.join(root, f), 'No reference found')

            elif count == 0:
                td_next  = ref_lst[0][0] - dto_date_orig
                next     = LatLon.LatLon(LatLon.Latitude(ref_lst[count][2][0][0]), LatLon.Longitude(ref_lst[count][2][0][1]))
                if td_next < td_threshold:
                    # GPS coords
                    gps_tag     = next

                    # Altitude
                    new_alt_ref = next_alt_ref
                    new_alt     = next_alt

                    print (os.path.join(root, f), 'using next point'.format(ref_lst[count][1]))

                else:
                    print (os.path.join(root, f), 'No reference found')
            else:
                td_prev  = dto_date_orig - ref_lst[count-1][0]
                prev = LatLon.LatLon(LatLon.Latitude(ref_lst[count-1][2][0][0]), LatLon.Longitude(ref_lst[count-1][2][0][1]))
                if td_prev < td_threshold:
                    # GPS coords
                    gps_tag     = prev

                    # Altitude
                    new_alt_ref = ref_lst[count-1][2][5] # prev_alt_ref
                    new_alt     = ref_lst[count-1][2][6] # prev_alt
                    print (os.path.join(root, f), 'using prev point'.format(ref_lst[count-1][1]))
                else:
                    print (os.path.join(root, f), 'No reference found')
                    continue # 2021/01/05
                
            # print ('GPS coords: ', gps_tag, type(gps_tag))
            (clat,clon) = map(float, gps_tag.to_string())
            if clat != 0.0 and clon != 0.0:
                # Put GPS time & date
                exif_dict['GPS'][7]  = tuple(tuple(y) for y in [[int(x),1] for x in dto_date_orig.strftime('%H:%M:%S').split(':')])
                exif_dict['GPS'][29] = bytes(dto_date_orig.strftime('%Y:%m:%d'), 'utf-8')

                # GPS location info
                gps_str  = [x.split() for x in gps_tag.to_string('d% %m% %S% %H') ]
                gps_secs = [Fraction(Decimal(gps_str[0][2])).limit_denominator(100), Fraction(Decimal(gps_str[1][2])).limit_denominator(100)]

                exif_dict['GPS'][1] = bytes(gps_str[0][3],'utf-8')
                exif_dict['GPS'][2] = ((int(gps_str[0][0]),1), (int(gps_str[0][1]),1), (gps_secs[0].numerator,gps_secs[0].denominator))
                exif_dict['GPS'][3] = bytes(gps_str[1][3], 'utf-8')
                exif_dict['GPS'][4] = ((int(gps_str[1][0]),1), (int(gps_str[1][1]),1), (gps_secs[1].numerator,gps_secs[1].denominator))

                # GPS Altitude
                exif_dict['GPS'][5] = new_alt_ref
                exif_dict['GPS'][6] = tuple(new_alt)

                # GPStimeStamp
                exif_dict['GPS'][7]  = ((dto_date_orig.hour+tzc,1), (dto_date_orig.minute,1), (dto_date_orig.second,1))
                exif_dict['GPS'][29] = bytes(dto_date_orig.strftime('%Y:%m:%d'), 'utf-8') # GPSDateStamp

                #print_exif_dict (exif_dict)
                
                exif_bytes = piexif.dump(exif_dict)
                piexif.insert(exif_bytes, os.path.join(root, f))



            



