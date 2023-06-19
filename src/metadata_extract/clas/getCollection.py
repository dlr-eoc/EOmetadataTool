import os

levels = {'0':'L0', 'L0':'L0', '1':'L1', 'L1':'L1', '2':'L2', 'L2':'L2', '1A':'L1A', '1B':'L1B', '1C':'L1C', '2A':'L2A', '3A':'L3A'}
S3_types = { 'OL':'OLCI', 'SR':'SRAL', 'SL':'SLSTR', 'SY':'Synergy', 'DO':'DORIS', 'MW':'MWR', 'AX':'AUX', 'GN':'GNSS' , 'TM':'TM'}
def collection(filename, productType):
    sensor = os.path.basename(filename)[0:2]
    if sensor == 'S1':
        level = levels.get(productType[8:9], 'AUX')
        collection = 'S1.AUX' if (productType[0:2] in ['GP','HK']) or (level == 'AUX') else 'S1.SAR.'+level
    elif sensor == 'S2':
        level = levels.get(productType[4:6], 'AX') if productType[0:3] == 'MSI' else 'AUX'
        collection = 'S2.AUX' if level == 'AUX' else 'S2.MSI.'+level
    elif sensor == 'S3':
        level = 'AUX' if productType[9:11] == 'AX' else levels.get(productType[3:4], 'AUX')
        product_type = S3_types.get(productType[0:2], 'AUX')
        collection = 'S3.AUX' if (level == 'AUX') or (product_type == 'AUX') else sensor + '.' + product_type + '.' + level
    else:
        collection = 'UNK'
    return collection

