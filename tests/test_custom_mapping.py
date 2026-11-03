import json
from extract import extract

class TestCustomMapping:

    def test_nc_metop(self, paths):
        id = "GOME_NO2_L3_20260101_METOPC_DLR_v1"
        custom_data_path = f"{paths['data_dir']}/scenes_for_custom_mappings"
        result = extract(f"{custom_data_path}/{id}.nc", f"{paths['mappings_dir']}/METOP.csv")
        expected_result = json.load(open(f"{paths['references_dir']}/extract/{id}.json", "r"))
        expected_result["filepath"]["Value"] = expected_result["filepath"]["Value"].replace("{{DATA_PATH}}", custom_data_path)

        assert result == expected_result

    def test_s5p_o3(self, paths):
        id = "S5P_DLR_NRTI_01_L3_O3_20260101"
        custom_data_path = f"{paths['data_dir']}/scenes_for_custom_mappings"
        result = extract(f"{custom_data_path}/{id}.nc", f"{paths['mappings_dir']}/S5P_O3.csv")
        expected_result = json.load(open(f"{paths['references_dir']}/extract/{id}.json", "r"))
        expected_result["filepath"]["Value"] = expected_result["filepath"]["Value"].replace("{{DATA_PATH}}", custom_data_path)

        assert result == expected_result
