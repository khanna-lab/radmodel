#!/bin/bash
#SBATCH --output=logs/radmodel_%j.out
#SBATCH --error=logs/radmodel_%j.err
#SBATCH --partition=batch
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G

set -euo pipefail

# get param path
paramPath="$1"
shift

processes=1
usage() {
  echo "usage: $0 {Parameter file} [-m memory] [-j jobname] [-T walltime] [-n nodes] [-o outfile]"
}

while getopts m:j:T:n:o: option; do
  case "${option}" in

  n) processes=${OPTARG} ;;
  o) outfile=${OPTARG} ;;
  *)
    usage >&2
    exit 1
    ;;
  esac
done

if [ ! "$paramPath" ]; then
    usage;
		exit 0;
fi

usage() {
  echo "usage: $0 {Parameter file} [-m memory] [-j jobname] [-T walltime] [-n nodes] [-o outfile]"
}

echo "Host: $(hostname)"
# echo "Job: ${SLURM_JOB_ID:-<none>}  Params: $PARAMS"
echo "Started: $(date -Is)"

# TO_REVIEW what do we want for n here?
mpirun -n "$processes" radmodel "$paramPath"
# mpirun -n "$SLURM_NTASKS" radmodel "$PARAMS"

echo "Finished: $(date -Is)"
