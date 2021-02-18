"""
End-to-end test: Fetches data from GIBS, creates output, stores it in /tmp and checks if output
is valid.
"""

from pathlib import Path

import geojson
import rasterio as rio
from blockutils.e2e import E2ETest

# Disable unused params for assert
# pylint: disable=unused-argument
def asserts(input_dir: Path, output_dir: Path, quicklook_dir: Path, logger):
    geojson_path = output_dir / "data.json"

    with open(str(geojson_path)) as f:
        feature_collection = geojson.load(f)

    img_filename = (
        output_dir / feature_collection.features[0]["properties"]["up42.data_path"]
    )
    with rio.open(img_filename) as dataset:
        meta = dataset.meta
        assert meta["width"] == 256
        assert meta["height"] == 256
        assert meta["count"] == 4


if __name__ == "__main__":
    e2e = E2ETest("nasa-modis")
    e2e.add_parameters(
        {
            "bbox": [18.433567, -33.917003, 18.439345, -33.912106],
            "imagery_layers": [
                "MODIS_Terra_CorrectedReflectance_TrueColor",
                "MODIS_Terra_NDVI_8Day",
            ],
            "time": "2018-01-01T00:00:00+00:00/2018-01-01T23:59:59+00:00"
        }
    )
    e2e.asserts = asserts
    e2e.run()
