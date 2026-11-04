#!/usr/bin/python3
import csv
import argparse
from .get_product_type import product_type as pt


def mapping_rule(target_product_type: str, product_types_2_rule_mapping: str) -> str:
    """Identify the name of the matching mapping file from a csv list and the product type.

    Args:
        target_product_type: String with the name of the product type.
        product_types_2_rule_mapping: String with the path to the csv list,
          containing matching product types and file names.

    Returns:
        A string with the path to the mapping file.
    """
    with open(product_types_2_rule_mapping, newline="") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=";")
        for row in reader:
            if row["ESAProductType"] == target_product_type:
                return row["RuleName"]
    raise Exception("Rule could not be found for %s" % target_product_type)


if __name__ == "__main__":
    # define command line argument
    parser = argparse.ArgumentParser(description="Sentinel metadata parser")
    parser.add_argument("scene", type=str, help="Path to Sentinel scene (zipped file or folder)")
    args = parser.parse_args()

    product_type = pt(args.scene)
    rule = mapping_rule(product_type, "mappings/ProductTypes2RuleMapping.csv")

    print(rule)
