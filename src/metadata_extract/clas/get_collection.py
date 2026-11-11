import os

levels = {
    "0": "L0",
    "L0": "L0",
    "1": "L1",
    "L1": "L1",
    "2": "L2",
    "L2": "L2",
    "1A": "L1A",
    "1B": "L1B",
    "1C": "L1C",
    "2A": "L2A",
    "3A": "L3A",
}
S3_types = {
    "OL": "OLCI",
    "SR": "SRAL",
    "SL": "SLSTR",
    "SY": "Synergy",
    "DO": "DORIS",
    "MW": "MWR",
    "AX": "AUX",
    "GN": "GNSS",
    "TM": "TM",
}


def collection(filename: str, product_type: str) -> str:
    """Constructs the collection name from filename and product type.

    Args:
        filename: A string containing the filename.
        product_type: A string with the product type.

    Returns:
        A string with the constructed collection name.
    """
    sensor = os.path.basename(filename)[0:2]
    if sensor == "S1":
        level = levels.get(product_type[8:9], "AUX")
        result = "S1.AUX" if (product_type[0:2] in ["GP", "HK"]) or (level == "AUX") else "S1.SAR." + level
    elif sensor == "S2":
        level = levels.get(product_type[4:6], "AX") if product_type[0:3] == "MSI" else "AUX"
        result = "S2.AUX" if level == "AUX" else "S2.MSI." + level
    elif sensor == "S3":
        level = "AUX" if product_type[9:11] == "AX" else levels.get(product_type[3:4], "AUX")
        product_type = S3_types.get(product_type[0:2], "AUX")
        result = (
            "S3.AUX"
            if (level == "AUX") or (product_type == "AUX")
            else sensor + "." + product_type + "." + level
        )
    else:
        result = "UNK"
    return result
