from typing import Dict
from mpi4py import MPI
import os

from repast4py.parameters import create_args_parser, init_params
from . import population
from . import core


def run(params: Dict, comm):

    fname = params["schedule_file"]
    schedule_id_map, schedule_data, risks = population.create_schedules(fname)
    fname = params["places_file"]
    places: population.Places = population.create_places(fname)
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
    for k, v in params.items():
        if isinstance(v, str) and "$this" in v:
            v = v.replace("$this", params_dir)
            params[k] = v
    run(params, MPI.COMM_WORLD)


if __name__ == "__main__":
    main()
