#!/usr/bin/python3
from extract import extract
from clas.get_collection import collection
from clas.get_product_type import product_type as pt
from clas.get_rule import mapping_rule
import argparse
import hashlib
import logging
import os
import pprint
import sys
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

# setup directories and library location
sys.path.append(os.path.dirname(__file__))

log = logging.getLogger("metadata_extract")
log.setLevel(logging.DEBUG)


def md5sum(filename, blocksize=65536):
    md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(blocksize), b""):
            md5.update(block)
    return md5.hexdigest()


def sha256sum(filename, block_size=65536):
    sha256 = hashlib.sha256()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            sha256.update(block)
    return sha256.hexdigest()


def filesize(filename):
    return os.stat(filename).st_size


# This function can be replaced during the extract() call
def dict_filler(data, name, data_type, value):
    data[name] = {"Value": value, "Type": data_type}
    return


# fmt: off
if __name__ == "__main__":
    logging.disabled = True
    # define command line argument
    parser = argparse.ArgumentParser(description="jinja templated metadata extractor")
    parser.add_argument("--scene", type=str, help="Path to product file (zipped file or folder)", required=True)  # noqa: E501
    parser.add_argument("--mapping", type=str, help="Mapping CSV file with attributes to ", required=False)
    parser.add_argument("--template", type=str, help="jinja template", required=False)
    parser.add_argument("-d", "--debug", help="debugging logs", action="store_const", dest="loglevel", const=logging.DEBUG, default=logging.WARNING)  # noqa: E501
    parser.add_argument("-v", "--verbose", help="verbose logs", action="store_const", dest="loglevel", const=logging.INFO)  # noqa: E501
    args = parser.parse_args()
# fmt: on

    # configure logging
    log_handler = logging.StreamHandler()
    log_format = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    log_handler.setFormatter(log_format)
    log_handler.setLevel(args.loglevel)
    log.addHandler(log_handler)

    context = {
        "filename": args.scene,
        "extract": extract,
        "now": str(datetime.now().isoformat()) + "Z",
        "dictFiller": dict_filler,
        "sha256sum": sha256sum,
        "md5sum": md5sum,
        "filesize": filesize}

    # allow mapping to be specified relative to CWD or within <__file__>/mapping/
    if args.mapping:
        mappings_file = (
            args.mapping
            if Path(args.mapping).exists()
            else str(Path(__file__).parent) + "/mappings/" + args.mapping
        )
    else:
        MAPPINGS = os.path.dirname(__file__) + "/mappings"
        product_type = pt(args.scene)
        collection_name = collection(args.scene, product_type)
        rule = mapping_rule(product_type, MAPPINGS + "/ProductTypes2RuleMapping.csv")
        mappings_file = MAPPINGS + "/" + rule + ".csv"

    # perform metadata extraction
    extracted_metadata = extract(args.scene, mappings_file, dict_filler)

    # add some standard metadata TODO: needs to be moved into mappings file
    try:
        dict_filler(extracted_metadata, "ProductType", "String", product_type)
        dict_filler(extracted_metadata, "Collection", "String", collection_name)
    except Exception:
        pass
    dict_filler(extracted_metadata, "contentLength", "Int64", filesize(args.scene))
    dict_filler(extracted_metadata, "publicationDate", "DateTimeOffset", context["now"])

    # this is passed to the template
    context["attributes"] = extracted_metadata

    # use context
    if args.template:
        file_loader = FileSystemLoader(".")
        env = Environment(loader=file_loader)
        template = env.get_template(args.template)
        output = template.render(context)
        print(output)
    else:
        pprint.pprint(extracted_metadata, width=120)
