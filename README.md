# EOmetadataTool
Table controlled Earth Observation metadata extractor and STAC tool

## Capabilities
* reads metadata from files in multiple formats like zip, gzip, tar, SAFE, NetCDF, or directory tree;
* extracts product metadata from one or more files;
* attribute list and extraction rules specified in a CSV file
* uses XPath expressions for the metadata extraction;
* adds XPath functions extensions for common text manipulations: join, regex, map, uppercase, date;
* creates any desired output format like STAC, EOP XML, JSON [23] using a jinja [22] template;
* allows using the tool as a python API to embed it in other applications.

## Usage
Example calls
* Dump of extracted metadata from a SAFE.zip package
  ```bash
  src/metadata_extract/extract.py --mapping src/metadata_extract/mappings/S1_L1L2.csv \
   tests/data/S1A_IW_GRDH_1SDV_20220621T075323_20220621T075348_043758_053961_0000.SAFE.zip
  ```
* Format the metadata using a jinja2 template - tool automatically determines sentinel-1, 2 or 3 product types following the file naming conventions and selects extraction mapping and output template
  ```
  src/metadata_extract/metadata_extract.py tests/data/S2A_MSIL1C_20230216T044851_N0509_R076_T46UEU_20230216T000000.SAFE.zip
  ```

* Mappings for S5p L2 and L3 are also included, but requires using --mapping and --template parameters
  ```
  src/metadata_extract/extract.py --mapping src/metadata_extract/mappings/S5P_TROPOMI_L2.csv \
    --template src/metadata_extract/templates/s5p_l2_stack.j2 \
   tests/data/S5P_OFFL_L2__O3_____20200303T013547_20200303T031717_12367_01_010107_20200306T053811.nc
  ```
  
### Usage with custom mapping tables
The `EOmetadataTool` can be used with custom mapping files. The files are required to consist of the columns
* `metadata`: The key for the extracted property in the resulting dictionary.
* `file`: A glob for the filename containing the meta information. E.g `manifest.safe` or `*.EOF` 
* `mappings`: The xpath for the property in the metafile.
* `datatype`: The type of the metadata. One of [the supported DataTypes](#list-of-supported-datatypes)

### List of supported DataTypes
* `String`
* `Geography`
* `Int`
* `Int64`
* `Double`
* `Boolean`
* `DateTime`
* `DateTimeOffset`



## Important to know
* Coordinates are in the format "Latitude,Longitude" (this is the default order for Sentinel-1 metadata). Points are separated by space. This order needs be reversed for GeoJSON output (e.g., for geoserver product.json/granules.json)

## Example execution in Python
```python
from metadata_extract/extract import extract
extracted_metadata = extract(args.scene, mappings_file, dict_filler)
pprint.pprint(extracted_metadata, width=120)

```
