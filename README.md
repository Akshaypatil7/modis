# MODIS data block for UP42
## Introduction

This is an example data block based on NASA's Global Imagery Browse Services (GIBS) providing access to three-band
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
 5. Required Python packages as specified in
    `blocks/s2-superresolution/requirements.txt`.

## Usage

### Local development HOWTO

Clone the repository zo a given `<directory>`:

```bash
git clone https://github.com/up42/modis.git <directory>
``` 

then do `cd <directory>`.

#### Install the required libraries

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