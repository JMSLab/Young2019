## Young (2019)

This repository conducts a partial replication of Table V of [Young (2019)](https://doi.org/10.1093/qje/qjy029) for the subset of applications for which data are publicly available.

Users can see the results of this partial replication [here](./output/tables/table_v.md).

For more granular information, [this directory](./output/derived/replication) includes data tables at the parameter, model, table, and paper level.

### Prerequisites

This repository is based on [JMSLab/Template](https://github.com/JMSLab/Template/tree/df4cfef8d1b0515fef84a2394835faceae34e496) and by default shares its dependencies and requirements.

The datastore is [Young2019](https://drive.google.com/drive/u/1/folders/0AMU9_S0mEvycUk9PVA).

### How to run

After installing prerequisites, type `scons`. 

### Parallelzation

To use multiple CPUs, type `scons -j <number of CPUs>`.

Details of computation are controlled by [dispatch.csv](./source/derived/replication/dispatch.csv).

Randomization $p$-values are calculated based on many replicates per application. These replicates can be divided across multiple CPUs. For each application, set the number of blocks (i.e., CPUs) and the number of replicates per block in the dispatch file.  Young (2019) uses 10,000 replicates per application, and by default, we allocate 1000 replicates split over 10 blocks.

Some applications use a bootstrap for inference. The `bstrap_reps` column of the dispatch file allows for specification of the number of bootstrap replicates when relevant. We set this to 500 by default.

