#!/usr/bin/python3
import csv
import argparse
from .getProductType import product_type

def mapping_rule(productType, product_types_2_rule_mapping):
    with open(product_types_2_rule_mapping, newline='') as csvfile:
        reader = csv.DictReader(csvfile,delimiter=';')
        for row in reader:
            if row['ESAProductType'] == productType:
                # print(row['ProductType'] + str(row['RuleName']))
                return row['RuleName']
    raise Exception("Rule could not be found for %s" % productType)

if __name__ == "__main__":
    # define command line argument
    parser = argparse.ArgumentParser(description='Sentinel metadata parser')
    parser.add_argument("scene", type=str, help="Path to Sentinel scene (zipped file or folder)")
    args = parser.parse_args()

    productType = product_type(args.scene)
    rule = mapping_rule(productType, 'mappings/ProductTypes2RuleMapping.csv')

    print(rule)
