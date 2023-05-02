#!/usr/bin/python3
import os
import argparse

def product_type(scene):
    scene = os.path.basename(scene)
    if scene.startswith('S1'):
        productType = scene.replace("_OPER","")[4:14].replace("_V2","")
    elif scene.startswith('S2'):
        if '_MSIL1C_' in scene:
            productType = 'MSI_L1C'
        elif '_MSIL2A_' in scene:
            productType = 'MSI_L2A'
        else:
            productType = scene[9:19]
    elif scene.startswith('S3'):
        productType = scene[4:15]
    elif scene.startswith('S5P'):
        productType = scene[0:4] + 'TROPOMI' + scene[8:20]
    else:
        raise Exception('Could not identify product level')
    return productType

if __name__ == "__main__":
    # define command line argument
    parser = argparse.ArgumentParser(description='Sentinel metadata parser')
    parser.add_argument("scene", type=str, help="Path to Sentinel scene (zipped file or folder)")
    args = parser.parse_args()

    productType = product_type(args.scene)

    print(productType)
