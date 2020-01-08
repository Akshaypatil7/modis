import os
import json
from gibs import GibsAPI


def run():
    imagery_layers = GibsAPI().get_dict_available_imagery_layers()
    for layer in imagery_layers:
        imagery_layers[layer]["WGS84BoundingBox"] = imagery_layers[layer][
            "WGS84BoundingBox"
        ].wkt

    with open(
        os.path.realpath(os.path.join(os.getcwd(), "available_imagery_layers.json")),
        "w",
    ) as out:
        json.dump(imagery_layers, out)


if __name__ == "__main__":
    run()
