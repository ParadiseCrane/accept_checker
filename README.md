# Accept Checker v1.0.0

Checker for the ACCEPT system

Works well with PascalABC, C++, Python3, Pypy3 and ... Java.

Tested on **Ubuntu 20.04.3 LTS**

## Requirements

- openjdk-17-jre-headles
- g++
- [pascalABC]('https://github.com/COOLIRON2311/pabcnetdeb') + mono
- python3
- pypy3

## Kafka Setup

sh building.sh

Then add path to kafka to .env

## Before start

`uv sync`

## Start

`uv run main.py`

## Pylint comments

Code becomes larger, so pylint becomes slower. If it is too slow, then remove it using `uv remove pylint`.

Also remove corresponding line in `setup_precommit.sh` and run it.
