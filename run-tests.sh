#!/bin/bash

export GENERATE_VCDS=1

python3 -m unittest pdmmic.pdm2pcm.PDM2PCMTest
