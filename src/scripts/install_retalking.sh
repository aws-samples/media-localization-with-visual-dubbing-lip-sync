#!/bin/bash
cur_dir=$PWD/src/retalking/code/
mkdir -p ${cur_dir}
tmp_dir=/tmp/retalking
mkdir -p ${tmp_dir}
rm -rf ${tmp_dir}
git clone https://github.com/OpenTalker/video-retalking ${tmp_dir}
rm -rf ${cur_dir}/models ${cur_dir}/third_part ${cur_dir}/utils 
mv ${tmp_dir}/models ${tmp_dir}/third_part ${tmp_dir}/utils ${cur_dir}/
rm -rf ${tmp_dir}
echo "Done downloading retalking repo"

