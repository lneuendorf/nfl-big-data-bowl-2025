#!/bin/bash

# Get the directory of the current script (scripts/setup_env.sh)
SCRIPT_DIR=$(dirname "$(realpath "$0")")

# Define the path to the environment.yml file
ENV_YML="$SCRIPT_DIR/../config/environment.yml"

# Step 1: Create the environment from environment.yml
echo "Creating conda environment from $ENV_YML..."
conda env create -f "$ENV_YML"

# Step 2: Activate the environment
conda activate bdb25

# Step 3: Add the environment as an IPython kernel for Jupyter
echo "Adding the conda environment as a Jupyter kernel..."
python -m ipykernel install --user --name bdb25 --display-name "bdb25"

echo "Environment setup complete. You can now select the kernel bdb25' in Jupyter notebooks."
