import os
import json
from gibs import GibsAPI

def run():
    layers = GibsAPI().get_list_available_layers()
    for layer in layers:
        layers[layer]['WGS84BoundingBox'] = layers[layer]['WGS84BoundingBox'].wkt

    with open(os.path.realpath(os.path.join(os.getcwd(), 'available_layers.json')), 'w') as out:
        json.dump(layers, out)

if __name__ == '__main__':
    run()
