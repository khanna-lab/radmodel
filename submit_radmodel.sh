#!/bin/bash
set -euo pipefail
walltime=02:00:00
memory=8G
jobname=""
num_cores=1
date=${date+%Y-%m-%d-T%H-%M-%S}
params="./params/radmodel_params.yaml"

usage() {
  echo "usage: $0 [-p parameter file] [-m memory] [-j jobname] [-T walltime] [-n nodes]

  Submit the batch script for radmodel. Uses default params from './params/radmode_params.yaml' if unspecified.
  "
}
# read params and sbatch opts
while getopts m:j:T:p:n:c: option; do
  case "${option}" in
  p) params=${OPTARG} ;;
  m) memory=${OPTARG} ;;
  j) jobname=${OPTARG} ;;
  T) walltime=${OPTARG} ;;
  c) num_cores=${OPTARG}  ;;
  *)
    usage >&2
    exit 1
    ;;
  esac
done

if [[ $jobname == "" ]]; then
  jobname="Analysis_$date"
fi

if [[ $params == "" ]]; then
  params="./params/radmodel_params.yaml"
  echo "Using default params"
fi

outPath="$HOME/scratch/radmodel"

prepSubmit() {
  mkdir -p "$finalPath"
  echo -e "\t$finalPath"
  sbatch --output="$finalPath"/slurm.out --error="$finalPath"/slurm.err -J "$jobname" -t "$walltime" --mem="$memory" -c "$num_cores" ./batch.sh "$params" -o "$finalPath"/results
}

echo -e "\tMaking directory in scratch"
mkdir -p "$outPath"
echo -e "\t $outPath"
finalPath=$outPath"/"$jobname
prepSubmit
