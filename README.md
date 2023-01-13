# EOmetadataTool
Table controlled Earth Observation metadata extractor and STAC tool

*NOTE: the code for this repository will soon be published.*

## Usage
Example call (recommended only for quick testing, not recommended for mass execution)
```bash
S1_DATA=//path/LTA-RFP-1_SampleSentinelProducts/SENTINEL-1
./metadata_extract.py Sentinel-1-Metadata_v2.csv L1 $S1_DATA/S1A_IW_GRDH_1SDV_20200121T201716_20200121T201741_030903_038C0F_DAEC.SAFE.zip
```

## Capabilities
* Loading of CSV xpath file is now separated (see function load_xpath)
* Read directly from zip and tar file based on file extension
* File path within CSV xpath file can include regular expression to find metadata xml file
* Xpath statement in CSV file supports now static/fixed values (example "=SENTINEL-2"): This value needs to start with an equals sign (=)
* Load CSV xpath file only once in mass execution

## Important to know
* Coordinates are in the format "Latitude,Longitude" (this is the default order for Sentinel-1 metadata). Points are separated by space. This order needs be reversed for GeoJSON output (e.g., for geoserver product.json/granules.json)

## Example execution in Python
```python
import sentinel_metadata_extract as sentinel_metadata

scene = '/mnt/data/esa-lta-rfp1/SENTINEL-2/S2B_OPER_MSI_L1C_TL_MPS__20191001T112642_A013418_T34UGA_N02.08.tar'
xpath_file = './Sentinel-2-Metadata_v2.csv'
xpath_csv_column = 'TL'

xpathQueries = sentinel_metadata.load_xpath(xpath_file, xpath_csv_column)
data = sentinel_metadata.extract(scene, xpathQueries)
```

## Example mass execution with Python
```bash
./example_extract.py ./Sentinel-1-Metadata_v2.csv L1 example_extract_s1.txt 
```
