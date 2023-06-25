#!/bin/bash
# python src/setup.py install
source .env/Scripts/Activate
pyinstaller --onefile src/__init__.py -n midas-recorder
# pyinstaller __init__.spec
