#!/bin/sh

module load python/3.11.0s-ixrhc3q
module load openmpi/4.1.2-s5wtoqb

MPI_LIB="/oscar/rt/9.2/software/0.20-generic/0.20.1/opt/spack/linux-rhel9-x86_64_v3/gcc-11.3.1/openmpi-4.1.2-s5wtoqbqirz4ivubo6uzp2ndglheablu/lib"
export LD_LIBRARY_PATH=$MPI_LIB:$LD_LIBRARY_PATH

#source /gpfs/data/akhann16/sfw/pyenvs/repast4py-py3.11/bin/activate
source /oscar/home/akhann16/sfw/pyenvs/radmodel-py3.11/bin/activate

# SWFIT-t stuff
#export PATH=/gpfs/data/akhann16/sfw/tcl-8.6.12/bin:/gpfs/data/akhann16/sfw/apache-ant-1.10.12/bin:$PATH
#export R_LIBS_USER=/gpfs/data/akhann16/sfw/rlibs/4.3.1
#SWIFT_T_HOME=/oscar/data/akhann16/sfw/gcc-11.3.1/openmpi-4.1.2/swift-t-02062024
#export PATH=$SWIFT_T_HOME/stc/bin:$PATH