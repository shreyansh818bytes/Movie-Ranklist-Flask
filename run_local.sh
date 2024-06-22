#! /bin/sh
# Activate virtual env
source venv/bin/activate

# Load the environment variables from the .env.local file
set -a
source config/.env.local
set +a

# Export the environment variables
export $(grep -v '^#' config/.env.local | xargs)

flask run
deactivate
