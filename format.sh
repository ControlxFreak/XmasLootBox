#!/bin/sh

# Run black and flake8 formatting
black .
flake8 --ignore E501 .