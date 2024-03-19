#!/usr/bin/python3
import os
import csv
import json
import re
import argparse
import logging
import pprint
import glob
import sys
import fnmatch
import tarfile
import zipfile
from datetime import datetime, timedelta
import gzip
from lxml import etree
from lxml import etree
from lxml.cssselect import ns
from osgeo import gdal
from pathlib import Path
from io import BytesIO

try:
  import netCDF4
except ImportError:
  netCDF4 = None

from dicttoxml import dicttoxml

if sys.version_info < (3, 7):
    from backports.datetime_fromisoformat import MonkeyPatch
    MonkeyPatch.patch_fromisoformat()

# Development and mounted
#from clas.getProductType import product_type
#from clas.getCollection import collection
#from clas.getRule import mapping_rule 

# Extract package helpers
sys.path.append(os.path.dirname(__file__))
from clas.getProductType import product_type
from clas.getCollection import collection
from clas.getRule import mapping_rule 

# Reads and parses mappings file (csv).
# Returns dictionary with metadata tag mappings (source tag name -> target tag name).

class load_mappings():
    def __new__(self, mappings_file, column = None):

        if not column:
            #column = os.path.splitext(os.path.basename(mappings_file))[0]
            column = "mappings"

        mappings_rules = dict()
        mappings_rules['static'] = dict()
        
        with open(mappings_file, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')

            for row in reader:
                #logging.debug("row_keys: %s", row.keys())
                if row[column] == '':
                    continue
                if row[column].startswith('='):
                    mappings_rules['static'][row['metadata']] = [row[column][1:], row['datatype']]
                    continue
                if row['file'] not in mappings_rules:
                    mappings_rules[row['file']] = dict()
                mappings_rules[row['file']][row['metadata']] = [row[column], row['datatype']]

        return mappings_rules

class metafile_readers():

    # Reads file (metafile) from zip file (inputfile).
    # Returns opened file stream.
    def read_from_zip(self, inputfile, metafile):
        archive = zipfile.ZipFile(inputfile, 'r')
        r = re.compile('(.*/)*' + metafile.replace('*', '.*'))
        files = archive.namelist()
        files = list(filter(r.match, files))
        if len(files) == 0:
            raise Exception("Metafile %s could not be found" % metafile)
        else:
            metafile = files[0]
            logging.debug("metadata file found in ZIP: %s", metafile)
        #else:
        #    metafile = os.path.join(os.path.basename(os.path.splitext(inputfile)[0]), metafile)
        metafile = archive.open(metafile)
        return metafile

    # Reads file (metafile) from tar file (inputfile).
    # Returns opened file stream.
    def read_from_tar(self, inputfile, metafile):
        archive = tarfile.open(inputfile, mode='r')
        r = re.compile('(.*/)*' + metafile.replace('**/','').replace('*', '[^/]*'))
        files = archive.getnames()
        files = list(filter(r.match, files))
        if len(files) == 0:
            raise Exception("Metafile %s could not be found" % metafile)
        else:
            metafile = files[0]
            logging.debug("metadata file found in TAR: %s", metafile)

        #else:
        #    metafile = os.path.join(os.path.basename(os.path.splitext(inputfile)[0]), metafile)
        metafile = archive.extractfile(metafile)
        return metafile

    # Reads file (metafile) from zip file (inputfile).
    # Returns opened file stream.
    def read_from_gzip(self, inputfile, metafile):
        logging.debug("metadata file found in gzip: %s", metafile)
        metafile = gzip.open(inputfile, 'rb')
        return metafile

    # Reads file (metafile) from folder (scenefolder).
    # Returns opened file stream.
    def read_from_folder(self, scenefolder, metafile):
        if len(glob.glob(scenefolder + "/" + metafile)) > 0:
            if metafile.endswith(".nc"):
                inputfiles = glob.glob(scenefolder + "/" + metafile)
                logging.debug("inputfiles: %s", inputfiles[0])
                metafile = inputfiles[0]
                logging.debug("metadata file found in DIR: %s", metafile)
                return metafile
        logging.debug("scene ordner: %s %s", scenefolder, metafile)
        if '*' in metafile:
            if os.path.isdir(scenefolder):
                metafiles = glob.glob(os.path.join(scenefolder, metafile), recursive=True)
                if len(metafiles) == 0:
                    raise Exception("Metafile %s could not be found" % metafile)
                else:
                    metafile = metafiles[0]
                    logging.debug("metadata file found in DIR: %s", metafile)
            elif fnmatch.fnmatch(scenefolder, metafile):
                # metafile pattern matches filename
                metafile = scenefolder
            else:
                raise Exception("Metafile " + metafile + " does not match filename " + scenefolder)
        else:
            metafile = os.path.join(scenefolder, metafile)
        metafile = open(metafile, 'r')
        return metafile

    # Reads file (metafile) from JPEG2000 file (inputfile) using GDAL.
    # Returns opened file stream.
    def read_from_jp2(self, inputfile, metafile):
        image = gdal.Open(inputfile)
        metafile = image.GetMetadata(metafile)[0]
        logging.debug("metadata file found in JP2000: %s", metafile)
        return BytesIO(bytes(metafile, encoding='ISO-8859-1'))

    def read_from_netcdf(self, inputfile, metafile):
        if not netCDF4.Dataset:
            logging.error("NetCDF library unavailable, extraction failed")
            return None
        if os.path.isdir(inputfile):
            inputfile = glob.glob(os.path.join(inputfile, metafile))[0]
        logging.debug("metadata file found in NetCDF: %s", inputfile)
        metafile = netCDF4.Dataset(inputfile)
        return metafile

# This function can be replaced during the extract() call
def dictFiller(data, name, type, value):
    #data[name] = {"Name": name, "Value": value, "Type": type}
    data[name] = {"Value": value, "Type": type}
    return

# Extract metadata from a given source file (xpath_file) for a specific sentinel scene (scene)
#
# scene: File containing source metadata (metadata which need to be mapped)
# csv_file: Mapping file / CSV-file which contains information on how to map metadata tags from "scene"
#
def extract(scene, csv_file, dict_filler = dictFiller):
    logging.debug("Scene: %s", scene)
    logging.debug("Mapping file: %s", csv_file)

    # Check input file or folder
    if not os.path.exists(scene):
        raise Exception('%s does not exist!' % scene)

    # Instantiate "readers" class
    readers = metafile_readers()
    logging.debug("readers: %s", type(readers))

    logging.debug("current workdir %s %s", os.getcwd(), csv_file)

    # Load metadata mapping.
    logging.debug("Looking for CSV: %s", csv_file)
    metadata_mapping = load_mappings(csv_file)

    # raise Exception("ERROR: mapping file missing " + csv_file)

    # Initialize output dictionary.
    mapped_metadata = dict()

    # Read scene filename and identifier
    filename = os.path.basename(scene)
    identifier = os.path.splitext(filename)[0].replace('.SAFE', '').replace('.EOF', '')

    # Fill in some initial information.
    dict_filler(mapped_metadata, 'filepath', 'String', scene)
    dict_filler(mapped_metadata, 'filename', 'String', filename)
    dict_filler(mapped_metadata, 'identifier', 'String', identifier)

    # data type specific parsers
    dataTypeStringParser = dict(Int=int, Int64=int, Double=float, String=str)

    # register extension functions for lxml.etree
    ns = etree.FunctionNamespace(None)
    ns['regex-capture'] = regex_capture
    ns['uppercase'] = uppercase
    ns['lowercase'] = lowercase
    ns['quote'] = quote
    ns['join'] = join_function
    ns['map'] = map_function
    ns['date_format'] = date_format
    ns['geo_pnt2wkt'] = geo_pnt2wkt
    ns['from_json'] = from_json_function
    ns['WKT'] = toWkt

    for metafile, queries in metadata_mapping.items():
        logging.debug("metafile: %s", metafile)
        logging.debug("queries: %s", queries)
            
        # Read metadata source file with corresponding reader (.zip, .tar, folder)
        if metafile != 'static':

            # Determine type of scene.
            scene_type = '.tar.gz' if scene.endswith('.tar.gz') else os.path.splitext(scene)[1].lower()
            metadata_type = '.tar.gz' if metafile.endswith('.tar.gz') else os.path.splitext(metafile)[1].lower()
            logging.debug("scene %s, metafile %s, type: %s", scene, metafile, scene_type)

            # read from metadata file from known types of packages
            if scene_type == '.nc' or metadata_type == '.nc':
                metadata_source = readers.read_from_netcdf(scene, metafile)
            elif os.path.isdir(scene):
                metadata_source = readers.read_from_folder(scene, metafile)
            elif scene_type == '.zip':
                metadata_source = readers.read_from_zip(scene, metafile)
            elif scene_type in ['.tar', '.tgz', '.tar.gz']:
                metadata_source = readers.read_from_tar(scene, metafile)
            elif scene_type == '.gz':
                metadata_source = readers.read_from_gzip(scene, metafile)
            elif scene_type == '.jp2':
                metadata_source = readers.read_from_jp2(scene, metafile)
            elif scene_type == '.json':
                metadata_source = readers.read_file(scene, metafile)
            elif os.path.isfile(scene):
                metadata_source = readers.read_from_folder(scene, metafile)
            else:
                logging.debug("")
                raise TypeError("Unknown scene %s of type %s", scene, scene_type)

            # parse into XML etree
            logging.debug("Input from: %s type: %s", metadata_source, type(metadata_source))
            if isinstance(metadata_source, netCDF4.Dataset):
                xmlstring = dicttoxml(metadata_source.__dict__)
                tree_root = etree.fromstring(xmlstring)
                tree = etree.ElementTree(tree_root)                    
            elif metadata_type == '.json':
                json_data = json.load(metadata_source)
                xmlstring = dicttoxml(json_data)
                tree_root = etree.fromstring(xmlstring)
                tree = etree.ElementTree(tree_root)
            else:
                tree = etree.parse(metadata_source)

            # cleanup XML namespace
            ns = tree.getroot().nsmap
            if None in ns:
                ns['general'] = ns[None]
                ns.pop(None)

        # process all mapping in this metadata file
        for name, (xpath, dataType) in queries.items():
            # skip commented lines in mapping
            if name[0] == '#':
                logging.debug("skipping name: %s | xpath: %s | dataType: %s", name, xpath, dataType)
                continue

            logging.debug("name: %s | xpath: %s | dataType: %s", name, xpath, dataType)

            # If target metadata entry is "static" --> store the value provided in the mapping-file source column.
            if metafile == 'static':
                value = product_type(filename) if xpath == 'productType' else xpath
                dict_filler(mapped_metadata, name, dataType, value)
                continue
            
            # attribute is skipped on empty xpath
            if len(xpath) == 0:
                continue

            if xpath == "filename":
                # logging.debug("- extension: Filename")
                value = filename
                dataType = "String"

            elif xpath == "now":
                # logging.debug("- extension: Now")
                value = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                dataType = "DateTime"

            else:
                # Check for value.
                try:
                    ##print("xpath:", xpath)
                    value_tmp = tree.xpath(xpath, namespaces=ns)
                    ##print("xpath returned:", value_tmp, len(value_tmp), type(value_tmp).__name__)
                    logging.debug("xpath returned: %s (%s)", value_tmp, type(value_tmp).__name__)
                    # resolve Element, list or string value
                    value = get_etree_element_value(value_tmp)
                except Exception as ex:
                    logging.warning("extracting %s with XPath: %s", name, xpath, exc_info=ex)
                    continue

            ##print("value for", name, 'with xpath:', xpath, "returned:", value)

            # Check whether target value was populated, otherwise continue with next metadata entry
            if not isinstance(value, float) and isinstance(value, list) and len(value) == 0 or value == None:
                continue

            logging.debug("typeHandling input dataType=%s: %s %s", dataType, value, type(value).__name__)

            if dataType == 'String':
                value = str(value)
            elif dataType in ['Int', 'Int64', 'Double']:
                value = dataTypeStringParser[dataType](str(value))
            elif dataType == 'Boolean':
                value = str(value[0]).upper()
            elif dataType in ['DateTime', 'DateTimeOffset']:
                try:
                    # ensure ISO8601 UTC DateTime always has a 'Z' at the end
                    value = str(value).replace('Z', '').replace('UTC=', '').replace(',', '') + "Z"
                except Exception as e:
                    logging.error("Failed to extract DateTime value from: %s", str(value), e)
                    value = '???'
            elif dataType == 'Geography':
                value = str(value)
            else:
                logging.warning("keeping unknown dataType=%s: %s %s", dataType, str(value), type(value).__name__)

            logging.debug("typeHandling output dataType=%s: %s %s", dataType, str(value), type(value).__name__)

            # Now write all information to the "data"-dictionary.
            dict_filler(mapped_metadata, name, dataType, value)

        # mappings per metadata file

    return mapped_metadata

def get_etree_element_value(value_tmp):
    if len(value_tmp) > 0:
        # take first match when xpath returned a list
        if isinstance(value_tmp, list):
            value = value_tmp[0]
            ##print("value type:", type(value))
            #if isinstance(value, tree._Element):
            try:
                value = value.text
            except:
                #print("ignoring value: ", value_tmp[0])
                value = str(value)
        else:
            value = str(value_tmp)
    else:
        logging.debug("skipping empty %s (%s)", value_tmp, type(value_tmp).__name__)
        return None
    return value

def save(data, outputfile):
    with open(outputfile, 'w') as out:
        json.dump(data, out, indent=4)

@ns
def uppercase(context, a):
    value = get_etree_element_value(a)
    logging.debug("uppercase for: %s", value)
    try:
      value = value.upper()
      logging.debug("uppercase produced: %s", value)
    except:
        #logging.warning("uppercase ignoring value: %s", value)
        return None
    return value

@ns
def lowercase(context, a):
    value = get_etree_element_value(a)
    logging.debug("lowercase for: %s", value)
    try:
        value = value.lower()
        logging.debug("lowercase produced: %s", value)
    except:
        #logging.warning("lowercase ignoring value: %s", value)
        return None
    return value

@ns
def quote(context, a):
    return [str(a[0] if len(a) == 1 else a)]

@ns
def regex_capture(context, a, regex_str):
    value = get_etree_element_value(a)
    logging.debug("regex_capture for: %s with %s", value, regex_str)
    value = re.search(regex_str, value).group()
    logging.debug("regex_capture retruns: %s", value)
    return value

@ns
def join_function(context, a, join_separator=', '):
    value = get_etree_element_value(a)
    try:
        return join_separator.join(value)
    except:
        #logging.warning("join_function ignoring value: %s", value)
        return value

@ns
def toWkt(context, a):
    # Convert lat,lon coordinate list into WKT (lon lat) list.
    # Returns a WKT POINT, LINESTRING or POLYGON.

    value = get_etree_element_value(a)

    logging.debug("toWkt - coordinates %s", value)

    # split string at every second space if no comma is contained (Sentinel-3)
    n = 2 if value.find(',') == -1 else 1
    coordinates = re.findall(" ".join(["[^ ]+"] * n), value)

    count = len(coordinates)
    # reverse "lat,lon" into "lon lat" (Sentinel-1 and -2)
    coordinateString = sep = ''
    for point in coordinates:
        lat,lon = re.split('[, ]', point)
        coordinateString += sep + lon + ' ' + lat
        sep = ', '
    # convert to POINT, LINESTRING or POLYGON
    if count == 1:
        wkt = 'POINT(' + coordinateString + ')'
    elif count == 2:
        wkt = 'LINESTRING(' + coordinateString + ')'
    else:
        if coordinates[0] != coordinates[count - 1]:
            # close polygon
            latlon = coordinates[0].split(',')
            coordinateString += ', ' + latlon[1] + ' ' + latlon[0]
        if count < 3:
            raise Exception('insufficient coordinate points ' + ' '.join(coordinates))
        wkt = 'POLYGON((' + coordinateString + '))'
    return wkt

@ns
def geo_pnt2wkt(context, a):
    if isinstance(a, list):
        coordinates = []
        for pnt in a:
            lat = pnt.xpath("*[local-name()='LATITUDE']")[0].text
            lng = pnt.xpath("*[local-name()='LONGITUDE']")[0].text
            coordinates.append('%s,%s' % (lat, lng))
        value = toWkt(context, coordinates)
    else:
        logging.warning("skipping Geo_Pnt extraction for %s (%s)", a, type(a).__name__)
        return None
    return value

@ns
def map_function(context, a, map_string):
    """
    map lookup translation
     examples:
       map(lowercase(my_boolean), '{"true":"True","yes":"True","1":"True","default":"False"}')
       map(quality, '{"PASSED":"NOMINAL","default":"DEGRADED"}')
       map(completeness, '{"100.0":"NOMINAL","default":"DEGRADED"}')
       map(lowercase(orbit_direction), '{"asc":"ASCENDING","ascending":"ASCENDING","default":"DESCENDING"}')
    """
    value = get_etree_element_value(a)
    logging.debug("map_function for: %s with %s", value, map_string)
    lookup = json.loads(map_string)
    value = lookup[value] if value in lookup.keys() else lookup['default']
    logging.debug("map_function decoded input: %s", value)
    return value

@ns
def from_json_function(context, a):
    value = json.loads(get_etree_element_value(a))
    logging.debug("from_json_function for: %s", value)
    return value


timedelta_regex = re.compile(r'^((?P<days>[\.\d]+?)d)?((?P<hours>[\.\d]+?)h)?((?P<minutes>[\.\d]+?)m)?((?P<seconds>[\.\d]+?)s)?$')
def parse_timedelta(time_str):
    """
    Parse a timedelta string e.g. (2h13m) into a timedelta object.
    """
    parts = timedelta_regex.match(time_str)
    if parts is not None:
        logging.warning("Could not parse any time information from '{}'." +
            "  Examples of valid strings: '8h', '2d8h5m20s', '2m4s'".format(time_str))
    time_params = {name: float(param) for name, param in parts.groupdict().items() if param}
    return timedelta(**time_params)   

@ns
def date_format(context, a, format='%Y-%m-%dT%H:%M:%SZ', date_add_delta=''):
    """
    simple date math with reformatting (e.g. for clipping and rounding)
    """
    value = get_etree_element_value(a)
    logging.debug("date_trim for: %s with %s", value, format)
    d = datetime.fromisoformat(value)
    delta = parse_timedelta(date_add_delta) if len(date_add_delta) > 0 else timedelta()
    value = datetime.strftime(d + delta, format)
    logging.debug("date_trim retruns: %s", value)
    return value


if __name__ == "__main__":
    logging.disabled = True
    # define command line argument
    parser = argparse.ArgumentParser(description='Sentinel metadata parser')
    parser.add_argument("--scene", type=str, help="Path to Sentinel scene (zipped file or folder) or filename of the NetCDF input file", required=True)
    parser.add_argument("--mapping", type=str, help="Mapping CSV file with attributes to ", required=True)
    parser.add_argument("--template", type=str, help="jinja template", required=False)
    parser.add_argument('-d', '--debug', help="debugging logs", action="store_const", dest="loglevel", const=logging.DEBUG, 
        default=logging.WARNING)
    parser.add_argument('-v', '--verbose', help="verbose logs", action="store_const", dest="loglevel", const=logging.INFO)
    args = parser.parse_args()

    # configure logging
    logging.basicConfig(level=args.loglevel, format='%(asctime)s %(levelname)s %(message)s')

    # allow mapping to be specified relative to CWD or within <__file__>/mapping/
    mappings_file = args.mapping if Path(args.mapping).exists() else str(Path(__file__).parent) + "/mappings/" + args.mapping

    # perform metadata extraction
    extracted_metadata = extract(args.scene, mappings_file, dictFiller)
    
    pprint.pprint(extracted_metadata, width=120)
    #print(json.dumps(extracted_metadata, indent=2))
