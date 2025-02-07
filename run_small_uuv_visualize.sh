#!/bin/bash

# Assign values to variables
BENCHMARK="uuv"
PATH_TO_VERISIG_PARSED_CSV="uuv_verisig_repaired_result_small.csv"  # replace it with the path of Verisig parsed result file you want
PATH_TO_SAMPLE_RESULT_CSV="uuv_sampling_repaired_result_small.csv"  # replace it with the name of sample result file you want
IF_SMALL=true

# Python execution
python3 visualization.py --benchmark="$BENCHMARK" --verisig_result_path="$PATH_TO_VERISIG_PARSED_CSV" --sampled_result_path="$PATH_TO_SAMPLE_RESULT_CSV" --small="$IF_SMALL"