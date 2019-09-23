"""
End-to-end test: Fetches data from GIBS, creates output, stores it in /tmp and checks if output
is valid.
"""

from pathlib import Path
import os

import geojson
import rasterio as rio

if __name__ == "__main__":
    OUTPUT_DIR = Path('/tmp/e2e_modis')
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FILES_TO_DELETE = Path(OUTPUT_DIR / 'output').glob('*.*')
    for file_path in FILES_TO_DELETE:
        file_path.unlink()

    RUN_CMD = """docker run -v /tmp/e2e_modis:/tmp \
                 -e 'UP42_TASK_PARAMETERS={"bbox":[18.433567,-33.917003,18.439345,-33.912106], "layers": ["MODIS_Terra_CorrectedReflectance_TrueColor"]}' \
                 -it nasa-modis"""
    os.system(RUN_CMD)

    GEOJSON_PATH = OUTPUT_DIR / 'output' / 'data.json'

    with open(str(GEOJSON_PATH)) as f:
        FEATURE_COLLECTION = geojson.load(f)

    IMG_FILENAME = "%s/%s" %(str(OUTPUT_DIR / 'output'),
                             FEATURE_COLLECTION.features[0]["properties"]["up42.data.aoiclipped"])
    with rio.open(IMG_FILENAME) as dataset:
        META = dataset.meta
        assert META['width'] == 256
        assert META['height'] == 256
        assert META['count'] == 3
