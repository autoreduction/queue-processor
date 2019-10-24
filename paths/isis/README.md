## ISIS Paths

### ISIS Reduction Path Manager
This is a specific implementation of `paths.reduction_path_manager.ReductionPathManager` for the ISIS facility.
It makes this architecture easier to use for ISIS by providing an interface that takes the location of the input data file, `instrument`,`propsal`(RB Number) and `run_number`.
These are then used to populate ISIS specific path templates such as the location of the reduction script in the Data Archive.
 
For more information on the `ReductionPathManager` view the `paths/README.md`