from typing import Dict
import os

from mpi4py import MPI
from repast4py.parameters import create_args_parser, init_params

from . import population
from . import core
from .layout import Layout


def run(params: Dict, comm):
    fname = params["schedule_file"]
    schedule_id_map, schedule_data, risks = population.create_schedules(fname)
    fname = params["places_file"]
    prison_layout = Layout.load_from_csv("data/")
    places: population.Places = population.Places(prison_layout.places_id_map, prison_layout.place_data)
    fname = params["residents_file"]
    residents = population.create_residents(fname, places.place_id_map, schedule_id_map)

    duration_matrix = core.create_duration_matrix(params)
    trans_matrix = core.create_trans_matrix(params["transition_matrix"])
    stoe = params["stoe"]

    model = core.Model(comm, schedule_data, residents, places, stoe, trans_matrix, duration_matrix,
                       params["random_seed"], params)
    model.run()


def main():
    parser = create_args_parser()
    args = parser.parse_args()
    params = init_params(args.parameters_file, args.parameters)
    params_dir = os.path.dirname(args.parameters_file)
    out_dir = params.get("output_dir", "output")
    for k, v in params.items():
        if isinstance(v, str):
            if "$this" in v:
                v = v.replace("$this", params_dir)
            if "$outdir" in v:
                v = v.replace("$outdir", out_dir)
            if "$HOME" in v:
                v = v.replace("$HOME", os.getenv("HOME"))
            if "$JOBNAME" in v:
                v = v.replace("$JOBNAME", os.getenv("SLURM_JOB_NAME"))
            params[k] = v
    os.makedirs(out_dir, exist_ok=True)
    run(params, MPI.COMM_WORLD)


if __name__ == "__main__":
    main()
    # schedule_id_map, schedule_data, risks = population.create_schedules(fname)
    # prison_layout = Layout.load_from_csv("./data")
    # places: population.Places = population.Places(prison_layout.places_id_map, prison_layout.place_data)
    # print(places.place_id_map)
