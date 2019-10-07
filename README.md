# MODIS AOI-Clipped data block
## Introduction

This is an example data block based on NASA's [Global Imagery Browse Services (GIBS)](https://earthdata.nasa.gov/eosdis/science-system-description/eosdis-components/gibs) providing access to three-band
MODIS imagery. This block can also provide other MODIS derived data such as the Normalized Difference Vegetation Index (NDVI) (rolling 8-day average) product or additional MODIS bands such as Corrected Reflectance for Bands 7-2-1.

## Block description

* Block type: data   
* Output type: AOIClipped (geo-referenced [GeoTIFF](https://en.wikipedia.org/wiki/GeoTIFF))
* Provider: [UP42](https://up42.com)
* Tags: MODIS, NASA, AOI clipped

### Inputs & outputs

The output is a [GeoTIFF](https://en.wikipedia.org/wiki/GeoTIFF) file.

### Block capabilities

This block has a single output capability, `up42.data.aoiclipped`.

## Requirements

 1. [git](https://git-scm.com/).
 2. [docker engine](https://docs.docker.com/engine/).
 3. [UP42](https://up42.com) account credentials.
 5. [GNU make](https://www.gnu.org/software/make/).
 5. [Python](https://python.org/downloads): version >= 3.7 &mdash; only
    for [local development](#local-development).

## Usage

### Clone the repository

Clone the repository:

```bash
git clone https://github.com/up42/modis.git
```

Then do `cd modis`.

### Installing the required libraries

First create a virtual environment either by using [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/)
or [virtualenv](https://virtualenv.pypa.io/en/latest/).
In the case of using virtualenvwrapper do:

```bash
mkvirtualenv --python=$(which python3.7) up42-modis
```

In the case of using virtualenv do:

```bash
virtualenv -p $(which python3.7) up42-modis
```

Activate the virtualenv:

```bash
workon up42-modis
```

After creating a virtual environment and activating it, all the necessary libraries can be installed on this environment by doing:

```bash
make install
```

### Run the tests

This project uses [pytest](https://docs.pytest.org/en/latest/) for
testing.  To run the tests, do as following:

```bash
make test
```

### Dockerizing the block

Build the docker image locally:

```bash
make build
```

Now you can run the end to end tests:

```bash
make e2e
```

### Pushing the block to the UP42 platform

For building the images you should tag the image in a way that can be
pushed to the UP42 docker registry, enabling you to run it as a custom
block. For that you need to pass your user ID (UID) in the `make`
command.

The quickest way to get that is just to go into the UP42 console and
copy & paste from the last clipboard that you get at the
[custom-blocks](https://console.up42.com/custom-blocks) page and after
clicking on **PUSH a BLOCK to THE PLATFORM**. For example, it will be
something like:

```bash
docker push registry.up42.com/<UID>/<image_name>:<tag>
```

First make sure the manifest is valid:

```bash
make validate
```

Now you can launch the image building using `make` like this:

```bash
make build UID=<UID>
```

You can additionally specify a custom tag for your image (default tag
is `nasa-modis:latest`):

```bash
make build UID=<UID> DOCKER_TAG=<docker tag>
```

#### Push the image to the UP42 registry

You first need to login into the UP42 docker registry.

```bash
make login USER=me@example.com
```

Where `me@example.com` should be replaced by your username, which is
the email address you use in UP42.

Now you can finally push the image to the UP42 docker registry:

```bash
make push UID=<UID>
```

Where `<UID>` is user ID referenced above.

Note that if you specified a custom docker tag when you built the image, you
need to pass it now to `make`.

```bash
make push UID=<UID> DOCKER_TAG=<docker tag>
```

After the image is pushed you should be able to see your custom block
in the [console](https://console.up42.dev/custom-blocks/) and you can
now use the block in a workflow.

### Available layers

Additionally, you can also update the file ``available_layers.json`` by running

```bash
make available-layers
```

## Support

 1. Open an issue here.
 2. Reach out to us on
      [gitter](https://gitter.im/up42-com/community).
 3. Mail us [support@up42.com](mailto:support@up42.com).
