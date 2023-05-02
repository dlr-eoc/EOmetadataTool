#!/usr/bin/python3
import argparse
import hashlib
import os
import pprint
import sys
import uuid
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

# setup directories and library location
sys.path.append(os.path.dirname(__file__))
from extract import extract
from clas.getCollection import collection
from clas.getProductType import product_type
from clas.getRule import mapping_rule


def md5sum(filename, blocksize=65536):
    md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(blocksize), b""):
            md5.update(block)
    return md5.hexdigest()

def sha256sum(filename, block_size=65536):
    sha256 = hashlib.sha256()
    with open(filename, 'rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
            sha256.update(block)
    return sha256.hexdigest()

def filesize(filename):
    return os.stat(filename).st_size

# This function can be replaced during the extract() call
#def dictFiller(data, name, type, value):
#    data[name] = value
#    return
def dictFiller(data, name, type, value):
    #data[name] = {"Name": name, "Value": value, "Type": type}
    data[name] = {"Value": value, "Type": type}
    return
    
if __name__ == "__main__":
    # define command line argument
    parser = argparse.ArgumentParser(description='jinja templated metadata extractor')
    parser.add_argument("--scene", type=str, help="Path to product file (zipped file or folder)", required=True)
    parser.add_argument("--mapping", type=str, help="Mapping CSV file with attributes to ", required=False)
    parser.add_argument("--template", type=str, help="jinja template", required=False)
    args = parser.parse_args()

    context = {}
    context['filename'] = args.scene
    context['extract'] = extract
    context['now'] = str(datetime.now().isoformat()) + 'Z'
    context['dictFiller'] = dictFiller
    context['sha256sum'] = sha256sum
    context['md5sum'] = md5sum
    context['filesize'] = filesize

    # allow mapping to be specified relative to CWD or within <__file__>/mapping/
    if args.mapping:
        mappings_file = args.mapping if Path(args.mapping).exists() else str(Path(__file__).parent) + "/mappings/" + args.mapping
    else:
        MAPPINGS = os.path.dirname(__file__) + '/mappings'
        productType = product_type(args.scene)
        collectionName = collection(args.scene, productType)
        rule = mapping_rule(productType, MAPPINGS + '/ProductTypes2RuleMapping.csv')
        mappings_file = MAPPINGS + "/" + rule + ".csv"
        
    # perform metadata extraction
    extracted_metadata = extract(args.scene, mappings_file, dictFiller)

    # add some standard metadata ## TODO: needs to be moved into mappings file
    if productType:
        dictFiller(extracted_metadata, 'ProductType', 'String', productType)
    if collectionName:
        dictFiller(extracted_metadata, 'Collection', 'String', collectionName)
    dictFiller(extracted_metadata, 'contentLength', 'Int64', filesize(args.scene))
    dictFiller(extracted_metadata, 'publicationDate', 'DateTimeOffset', context['now'])

    # this is passed to the template
    context['attributes'] = extracted_metadata

    # use context
    #pprint.pprint(context)
    if args.template:
        file_loader = FileSystemLoader('.')
        env = Environment(loader=file_loader)
        template = env.get_template(args.template)
        output = template.render(context)
        print(output)
    else:
        pprint.pprint(extracted_metadata, width=120)

