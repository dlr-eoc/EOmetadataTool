#!/usr/bin/python3
import csv


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
