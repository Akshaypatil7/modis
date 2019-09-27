### Dockerfile to build modis block.

FROM python:3.7.1-stretch
ARG manifest
LABEL "up42_manifest"=$manifest

# Working directory setup.
WORKDIR /block
COPY requirements.txt /block
RUN pip install -r requirements.txt

# Copy the code into the container.
COPY src /block/src

CMD ["python3", "/block/src/run.py"]