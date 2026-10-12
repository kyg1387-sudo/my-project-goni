#!/bin/bash
cd "$(dirname "$0")"
cat ashita-kara-final.mp4.part-* > ashita-kara-final.mp4
echo "Done: ashita-kara-final.mp4"
