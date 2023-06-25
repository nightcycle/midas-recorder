#!/bin/bash
source .env/Scripts/Activate
sh scripts/to_exe.sh
dist/midas-recorder.exe run 2015093382 -o data -interval 5 -group 4181328