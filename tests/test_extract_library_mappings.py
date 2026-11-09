#!/bin/python3
"""
Testing code for extract.py
"""

from extract import extract
from clas.get_product_type import product_type as pt
from clas.get_rule import mapping_rule
import os
import sys
import json
from pathlib import Path
import jsondiff

# setup directories and library location
BASEDIR = Path(os.path.dirname(__file__)).absolute()
LIBDIR = str(BASEDIR.joinpath("../src/metadata_extract").resolve())

# test specimen path
sys.path.append(LIBDIR)

MAPPINGS = LIBDIR + "/mappings"

# test data and references
DATADIR = BASEDIR.joinpath("data/scenes_for_library_mappings")
REFDIR = BASEDIR.joinpath("references/extract")


# locate all zip test data files and map to its json reference
def pytest_generate_tests(metafunc):
    scenes = []
    for scene in list(DATADIR.glob("*.zip")) + list(DATADIR.glob("**/*.nc")):
        # basename without extension
        identifier = scene.name
        if identifier.index("."):
            identifier = identifier[: identifier.rfind(".")]
        # reference file
        reference = REFDIR.joinpath(identifier + ".json")
        # add to list
        scenes.append([str(scene), str(reference)])
    # create a py.test call for each scene
    metafunc.parametrize("input_scene, output_reference", scenes)


def test_extract(input_scene, output_reference):
    assert Path(input_scene).exists()
    assert Path(output_reference).exists()

    # determine mapping dictionary file
    if "s5p/" in input_scene and os.path.isfile(os.path.dirname(input_scene) + "/mappings.csv"):
        # TODO: make less environment dependent
        csv_file = os.path.dirname(input_scene) + "/mappings.csv"
    else:
        product_type = pt(input_scene)
        rule = mapping_rule(product_type, MAPPINGS + "/ProductTypes2RuleMapping.csv")
        csv_file = MAPPINGS + "/" + rule + ".csv"

    # run extract function
    data = extract(input_scene, csv_file)
    assert jsondiff.diff(data, json.load(Path(output_reference).open()))
