#!/bin/bash
cur_dir=$PWD/src/layers/ffmpeg/
mkdir -p $cur_dir
tmp_dir=/tmp/ffmpeg
mkdir -p ${tmp_dir}
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -P ${tmp_dir}
cd ${tmp_dir}
tar -xf ffmpeg-release-amd64-static.tar.xz
mv ffmpeg-*-amd64-static $cur_dir/bin
rm -rf ffmpeg-*-amd64-static/
