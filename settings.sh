#!/bin/sh

module load python/3.11.11-5e66
module load openmpi/4.1.8-iqkf

MPI_LIB="/oscar/rt/9.6/25/spack/x86_64_v3/openmpi-4.1.8-iqkfiqkhvkeeixa6xvp2o7nuidh6x6x3/lib"
PYTHON_LIB="/oscar/rt/9.6/25/spack/x86_64_v3/python-3.11.11-5e66epfh6bxt72bivuccajllo5eixfnq/lib"
export LD_LIBRARY_PATH=$MPI_LIB:$PYTHON_LIB:$LD_LIBRARY_PATH

# silence cuda related warnings
export OMPI_MCA_opal_warn_on_missing_libcuda=0

# Fix UCX memory hook warning
export OMPI_MCA_opal_common_ucx_opal_mem_hooks=1

# Skip InfiniBand transport. Cluster ulimit -l (8192 KB) is too low for UCX to
# register pinned memory on IB, which otherwise floods stderr with ibv_reg_mr
# errors. TCP + shared memory is sufficient for single-node mpirun -n 1 runs.
export UCX_TLS=tcp,sm,self
export UCX_LOG_LEVEL=error
export OMPI_MCA_btl=^openib

#source /gpfs/data/akhann16/sfw/pyenvs/repast4py-py3.11/bin/activate
#source /oscar/home/akhann16/sfw/pyenvs/radmodel-py3.11/bin/activate  # old per-user venv
source /oscar/data/akhann16/sfw/pyenvs/radmodel-py3.11/bin/activate

# SWFIT-t stuff
#export PATH=/gpfs/data/akhann16/sfw/tcl-8.6.12/bin:/gpfs/data/akhann16/sfw/apache-ant-1.10.12/bin:$PATH
#export R_LIBS_USER=/gpfs/data/akhann16/sfw/rlibs/4.3.1
#SWIFT_T_HOME=/oscar/data/akhann16/sfw/gcc-11.3.1/openmpi-4.1.2/swift-t-02062024
#export PATH=$SWIFT_T_HOME/stc/bin:$PATH

# To run - on the compute node, do:
## mpirun -n 1 radmodel params/radmodel_params.yaml
