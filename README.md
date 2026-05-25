# radmodel
Repository for code related to radx-up r21 radx modeling


## Setup (Oscar, shared venv)

The project ships with a group-shared virtual environment at:

```
/oscar/data/akhann16/sfw/pyenvs/radmodel-py3.11
```

Members of the `ccv-akhann16` group can use it directly. To load modules, set
`LD_LIBRARY_PATH`, export the MPI/UCX runtime tuning, and activate the venv in
one step:

```bash
source settings.sh
```

This loads `python/3.11.11-5e66` and `openmpi/4.1.8-iqkf`. The UCX env vars in
`settings.sh` force TCP + shared-memory transport, which avoids the
`ibv_reg_mr ... Cannot allocate memory` flood that otherwise occurs on Oscar
compute nodes (the default `ulimit -l` is too low for UCX to pin memory on
InfiniBand).

## Installation (your own venv)

If you'd rather have an isolated install:

```bash
module load python/3.11.11-5e66 openmpi/4.1.8-iqkf
python3 -m venv ~/.venvs/radmodel-py3.11
source ~/.venvs/radmodel-py3.11/bin/activate
export CC=mpicc MPICC=mpicc          # required: mpi4py + repast4py build from source
pip install -r requirements.txt
pip install -e .
```

`CC=mpicc` is required — without it, `repast4py`'s build fails with
`Error: MPI compiler is not specified`.

With `-e` any changes you make to the radmodel code will be reflected in the
virtual environment install.

### Rebuilding the shared venv

When Oscar's module versions change again, the shared venv needs to be rebuilt
with the same steps as above, targeting
`/oscar/data/akhann16/sfw/pyenvs/radmodel-py3.11`. Update the module names in
`settings.sh` (and the spack paths in `MPI_LIB` / `PYTHON_LIB`) to match.

## Testing and Running

1. `source settings.sh` (or activate your own venv with the same modules loaded)
2. Run with `radmodel`

```
❯ radmodel -h
usage: radmodel [-h] parameters_file [parameters]

positional arguments:
  parameters_file  parameters file (yaml format)
  parameters       json parameters string

options:
  -h, --help       show this help message and exit

❯ radmodel params/radmodel_params.yaml
{'stop.at': 2880.2}
```

3. Test with `pytest`

```
❯ pytest
============================= test session starts ==============================
platform linux -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0
rootdir: /oscar/home/akhann16/code/radmodel
configfile: pyproject.toml
collected 17 items

tests/test_core.py .................                                     [100%]

============================== 17 passed in 5.28s ==============================
```

4. Running specific tests:

```
pytest tests/test_core.py::test_create_schedule
```

Or to run a few related ones with -k keyword matching:

```
pytest tests/test_core.py -k "select_next_place"
```

To print names of tests, do:

```
(radmodel-py3.11) [akhann16@node2335 radmodel]$ pytest tests/test_core.py -k "create" -v
========================================================== test session starts ===========================================================
platform linux -- Python 3.11.11, pytest-8.3.2, pluggy-1.5.0 -- /oscar/data/akhann16/sfw/pyenvs/radmodel-py3.11/bin/python3
cachedir: .pytest_cache
rootdir: /oscar/home/akhann16/code/radmodel
configfile: pyproject.toml
plugins: anyio-4.9.0
collected 17 items / 14 deselected / 3 selected                                                                                          

tests/test_core.py::test_create_schedule PASSED                                                                                    [ 33%]
tests/test_core.py::test_create_places PASSED                                                                                      [ 66%]
tests/test_core.py::test_create_residents PASSED    
```

To print output from individual tests, do:

```
pytest tests/test_core.py::test_create_schedule -v -s
```


## Output directory

Each run writes `counts.csv` and `counts_by_place.csv` to a directory
controlled by the `output_dir` param in `params/radmodel_params.yaml`. The
counts paths use a `$outdir` token that expands to whatever `output_dir` is
set to (default: `output/default`). The directory is created on demand.

To send a one-off run to its own directory, override on the command line:

```bash
radmodel params/radmodel_params.yaml '{"output_dir": "output/exp_baseline"}'
```

## Submitting a Slurm job

`submit_radmodel.sh` wraps the above for batch submission:

```bash
sbatch submit_radmodel.sh                              # uses params/radmodel_params.yaml
sbatch submit_radmodel.sh params/some_other.yaml       # different params file
```

The script automatically scopes each job's output to `output/run_<SLURM_JOB_ID>/`
(or `output/run_local_<timestamp>/` if invoked outside Slurm), so concurrent
runs and successive experiments don't overwrite each other. Job stdout/stderr
go to `logs/radmodel_<jobid>.{out,err}`. Defaults: 1 node, 1 task, 8 GB, 2 h
on the `batch` partition — tune `--mem`, `--time`, and `--ntasks` in the
`#SBATCH` headers as needed.

Monitor and inspect:

```bash
squeue -u $USER                                 # job status
tail -f logs/radmodel_<jobid>.out               # live output
sacct -u $USER --starttime today \
      --format=JobID,JobName,State,Elapsed,ExitCode    # past jobs
seff <jobid>                                    # post-run RAM/CPU efficiency
```

## VSCODE Set up
To use the correct Python environment in VS Code, select the following as your Python interpreter:

```
/oscar/home/akhann16/code/radmodel/launch_radmodel.sh
```


This wrapper script sources the project’s `settings.sh`, which sets `LD_LIBRARY_PATH` and activates the environment.



## Funding Information
[R21 MD 019388](https://reporter.nih.gov/search/3xP1HNXGDkKYlxiG9LbyJA/project-details/10933019)  
