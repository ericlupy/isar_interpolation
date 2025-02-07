#!/bin/bash

# Assign values to variables
BENCHMARK="uuv"
PATH_TO_CONTROL_NETWORK_YML="uuv_output/repaired_network.yml" # replace it with the network to be verified, e.g. the repaired network
PATH_TO_PARTITION_CSV="uuv_initial_state_regions.csv"
PATH_TO_SAMPLE_RESULT_CSV="uuv_sampling_repaired_result.csv" # replace it with the name of sample result file you want
N_SAMPLES=10
PATH_TO_VERISIG="verisig"
PATH_TO_VERISIG_OUTPUT="uuv_verisig_repaired_output" # replace it with the path of Verisig output you want
PATH_TO_VERISIG_PARSED_CSV="uuv_verisig_repaired_result.csv" # replace it with the path of Verisig parsed result file you want
RATIO=0.25

# Check outcome of sampled initial states
python3 sample_states_in_regions.py --benchmark="$BENCHMARK" --network="$PATH_TO_CONTROL_NETWORK_YML" --initial_state_regions_path="$PATH_TO_PARTITION_CSV" --sampled_result_path="$PATH_TO_SAMPLE_RESULT_CSV" --num_samples_per_region="$N_SAMPLES"

# Call Verisig
python3 verisig_call.py --benchmark="$BENCHMARK" --network="$PATH_TO_CONTROL_NETWORK_YML" --verisig_path="$PATH_TO_VERISIG" --verisig_output_path="$PATH_TO_VERISIG_OUTPUT" --cpu_ratio="$RATIO" --initial_state_regions_path="$PATH_TO_PARTITION_CSV"
python3 verisig_parse_results.py --benchmark="$BENCHMARK" --network="$PATH_TO_CONTROL_NETWORK_YML" --verisig_output_path="$PATH_TO_VERISIG_OUTPUT" --verisig_parsed_csv="$PATH_TO_VERISIG_PARSED_CSV" --initial_state_regions_csv="$PATH_TO_PARTITION_CSV"