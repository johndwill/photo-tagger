#!/bin/zsh

# This script is used to tag photos with the location and time of capture.
# It uses the exifread library to read the EXIF data from the photos.
# It uses the geopy library to reverse geocode the coordinates to a location string.
# It uses the PIL library to resize the image to 16:9 and overlay the text.
# It uses the sys library to read the command line arguments.
# It uses the pathlib library to create the output path.
# It uses the os library to create the output directory if it doesn't exist.
# It uses the datetime library to format the time string.
# It uses the geopy library to reverse geocode the coordinates to a location string.
# It uses the PIL library to resize the image to 16:9 and overlay the text.
# It uses the sys library to read the command line arguments.

source ./venv/bin/activate

# dir="/Users/JohnWilliams/imgs/2016-River Cruise"
dir="/Users/JohnWilliams/imgs/2026-random"
output_dir="${dir}/tagged"
mkdir -p $output_dir

print "Tagging images in $dir"

for file in $dir/*; do
    if [ -f $file ]; then
        base_file=$(basename $file)
        output_file="${output_dir}/${base_file%.*}_tagged.png"

        if [[ $base_file == *tagged* || -f "${output_file}" ]]; then
            continue
        fi
        echo Tagging $file to $output_file
        python photo_tagger.py $file $output_file
    fi
done