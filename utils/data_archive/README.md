# utils.data_archive
Contains the ``ArchiveExplorer`` and ``DataArchiveCreator``. For full examples and
available functions in these class see the source code.

## ArchiveExplorer
This class used to "explore" (find file and directory locations) within an instance
of the ISIS data archive. The directory structure of the ISIS data archive is assumed
to be constant and to match the following:

```plantuml
digraph ArchiveStructure {
DataArchive -> NDXGEM
DataArchive -> NDXPOLARIS
DataArchive -> NDXWISH
DataArchive -> "...."
NDXGEM -> user -> scripts -> autoreduction -> "reduce.py"
                             autoreduction -> "reduce_vars.py"

NDXGEM -> Instrument -> logs -> journal -> "SUMMARY.txt"
                        logs -> "lastrun.txt"

Instrument -> data -> cycle_18_1 -> autoreduced
                      cycle_18_1 -> "GEM1234.nxs"
                      cycle_18_1 -> "GEM1234.raw"
              data -> cycle_18_2
              data -> "..."
}
```

On initialisation of the ``ArchiveExplorer`` you are required to provide a file path
to the base directory of the data archive. In the example above, this would be the
``DataArchive`` directory. The ArchiveExplorer object can then be used to find
specific files or directories in the data archive:

```python
import datetime
import time
from utils.data_archive.archive_explorer import ArchiveExplorer

archive_explorer = ArchiveExplorer('path/to/base-directory')

# Return lastrun.txt for Instrument
last_run = archive_explorer.get_last_run_file('GEM')
# Get the file path for the most recent cycle in the GEM folder
archive_explorer.get_current_cycle_directory('GEM')

# Get any GEM runs that have been added to the directory in the last 2 seconds
cutoff_time = datetime.datetime.now()
time.sleep(2)
archive_explorer.get_most_recent_run_since('GEM', cutoff_time)
```

## DataArchiveCreator
The ``DataArchiveCreator`` is a way of creating fake data archives that can be used
in testing scenarios. This class quite often will be used in tandem with the ``ArchiveExplorer``.
The structure of the fake archive will mirror that shown above for the real archive.
On initialisation, the ``DataArchiveCreator`` will need a base directory as input.
This will be where the ``data-archive`` directory is created. Once initialised, the object
can be used to create the archive and files within it. The example below shows this:
```python
from utils.data_archive.data_archive_creator import DataArchiveCreator

data_archive_creator = DataArchiveCreator('base-directory')

# Create a data archive that contains cycles for GEM, POLARIS and WISH
# The cycles will include 17_1, 17_2, 17_3, 17_4, 18_1, 18_2
data_archive_creator.make_data_archive(instruments=['GEM', 'POLARIS', 'WISH'],
                                       start_year=17,
                                       end_year=18,
                                       current_cycle=2)

# Add a fake nxs file to the most recent GEM cycle dir
data_archive_creator.add_data_to_most_recent_cycle(instrument='GEM',
                                                   data_files=['test-file.nxs'])
# Add a summary file to POLARIS
data_archive_creator.add_journal_file(instrument='POLARIS',
                                      file_contents='hello world')

```
