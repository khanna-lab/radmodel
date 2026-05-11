#!/bin/bash
#SBATCH --job-name=radmodel
#SBATCH --output=logs/radmodel_%j.out
#SBATCH --error=logs/radmodel_%j.err
#SBATCH --partition=batch
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G

set -euo pipefail

REPO="/oscar/home/akhann16/code/radmodel"
PARAMS="${1:-$REPO/params/radmodel_params.yaml}"

cd "$REPO"
mkdir -p logs

source settings.sh

echo "Host: $(hostname)"
echo "Job: ${SLURM_JOB_ID:-<none>}  Params: $PARAMS"
echo "Started: $(date -Is)"

mpirun -n "$SLURM_NTASKS" radmodel "$PARAMS"

echo "Finished: $(date -Is)"
