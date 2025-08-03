## Young (2019)

This repository replicates some of the main results in [Young (2019)](https://doi.org/10.1093/qje/qjy029) for a subset of the applications considered therein. Run `scons` to compile the repository. Compilation produces tables at the parameter, model, table, and paper level which can be found in `output/derived/replication` (see [here](https://github.com/JMSLab/Young2019/tree/69a002be49942379064fd2e3d6b56670faf90cfa/output/derived/replication), for example). Compilation also produces a partial replication of Table V in Young (2019), which can be found at `output/tables/table_v.md` (see [here](https://github.com/JMSLab/Young2019/blob/69a002be49942379064fd2e3d6b56670faf90cfa/output/tables/table_v.md), for example).

The parameters governing compilation are set in `source/derived/replication/dispatch.csv`. Randomization $p$-values are calculated based on many replicates per application. These replicates can be divided across multiple CPUs. For each application, set the number of blocks (ie, CPUs) and the number of replicates per block in the dispatch file. In [this](https://github.com/JMSLab/Young2019/blob/69a002be49942379064fd2e3d6b56670faf90cfa/source/derived/replication/dispatch.csv) dispatch file, all applications included in the datastore are allocated 1,000 replicates split over 10 blocks. Young (2019) uses 10,000 replicates per application. To compile the repository using multiple CPUs, run `scons -j <number of CPUs>`. 

Additionally, some of the applications considered in Young (2019) use a bootstrap for inference. The `bstrap_reps` column of the dispatch file allows for specification of the number of bootstrap replicates when relevant. This is set to 500 by default.

### Prerequisites

This repository is based on [JMSLab/Template](https://github.com/JMSLab/Template/tree/df4cfef8d1b0515fef84a2394835faceae34e496) and by default shares its dependencies and requirements.

The datastore is [Young2019](https://drive.google.com/drive/u/1/folders/0AMU9_S0mEvycUk9PVA).

