#!/usr/bin/python3
import os
import argparse


def product_type(scene: str) -> str:
    """Constructs the product type from the scene name.

    Args:
        scene: Name of the scene.

    Returns:
       A string with the product type.
    """
    scene = os.path.basename(scene)
    if scene.startswith("S1"):
        result = scene.replace("_OPER", "")[4:14].replace("_V2", "")
    elif scene.startswith("S2"):
        if "_MSIL1C_" in scene:
            result = "MSI_L1C"
        elif "_MSIL2A_" in scene:
            result = "MSI_L2A"
        else:
            result = scene[9:19]
    elif scene.startswith("S3"):
        result = scene[4:15]
    elif scene.startswith("S5P"):
        result = scene[0:4] + "TROPOMI" + scene[8:20]
    else:
        raise Exception("Could not identify product level")
    return result


if __name__ == "__main__":
    # define command line argument
    parser = argparse.ArgumentParser(description="Sentinel metadata parser")
    parser.add_argument("scene", type=str, help="Path to Sentinel scene (zipped file or folder)")
    args = parser.parse_args()

    productType = product_type(args.scene)

    print(productType)
