# MODIS data block for UP42
## Introduction

This is an example data block based on NASA's [Global Imagery Browse Services (GIBS)](https://earthdata.nasa.gov/eosdis/science-system-description/eosdis-components/gibs) providing access to three-band
MODIS imagery.

## Block description
* Block type: data   
* Output type: AOIClipped (geo-referenced [GeoTIFF](https://en.wikipedia.org/wiki/GeoTIFF))
* Provider: [UP42](https://up42.com)

## Requirements

 1. [git](https://git-scm.com/).
 2. [docker engine](https://docs.docker.com/engine/).
 3. [UP42](https://up42.com) account credentials.
 4. [Python](https://python.org) 3.5 or later.

## Usage

### Local development HOWTO

Clone the repository to a given `<directory>`:

```bash
git clone https://github.com/up42/modis.git <directory>
``` 

then do `cd <directory>`.

### Installing the required libraries

First create a virtual environment either by using [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/) 
or [virtualenv](https://virtualenv.pypa.io/en/latest/).
In the case of using virtualenvwrapper do:

```mkvirtualenv --python=$(which python3.7) up42-modis```

In the case of using virtualenv do:

````
virtualenv -p $(which python3.7) up42-modis
````

After creating a virtual environment and activating it, all the necessary libraries can be installed on this environment by doing:

```bash
make install
```

You can run all unit tests with:

```bash
make test
```


### Dockerizing the block and pushing it to the UP42 platform

In order to publish the block on the platform several steps are necessary which are described on the platform itself.
Before doing that it is recommended practice to validate the manifest and execute a local end-to-end test.

First the manifest needs to be validated

```bash
make validate
```

Next build the docker image

```bash
make build-image
```

Finally you can run the end-to-end test

```bash
make e2e
```

If none of the commands throws any errors you can push the block to the UP42 platform as a custom block.