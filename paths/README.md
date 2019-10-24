## Paths

The paths module is designed to add functionality for storing and manipulating paths or collections of paths. 
Previously paths have been stored as strings. However, this was inadequate and could lead to confusion with poorly named variables.

* [Path](#path)
* [Path Manipulation](#path-man)
* [Collections](#collections)
* [Reduction Path Manager](#red-path-man)

### <a name="path">Path</a>
The new `Path` class has 2 inputs: `value` and `type`.
Here, `value` is the string representation of the path, and `type` is either `file` or `directory` (shorthand `dir` for directory  is also allowed).

```
log_file_path = Path('/some/file/path/test.log', 'file')
``` 
In addition to storing paths, this class also has a validate function to check:
 * `existance`
 * `absoluteness`
 * `readablility`
 * `writablility`
 * `Path.type`

By default the path must, exist, be absolute, be readable and match the `path.type` given at initialisation. Write permissions are not checked by default.
Any of these checks can be overridden in the  `__init__`.

Two `Path` objects are said to be equal if the `value` and `type` are the same. In the following example `path1` and `path2` are equal:
```
path1 = Path('/test/dir', 'dir')
path2 = Path('/test/dir', 'dir')

path1 == path2 -> True
```

### <a name="path-man">Path Manipulation</a>
Contains a set of functions that are designed to manipulate string paths (e.g. `Path.value` or a plain string representing a path).
These functions include:
 * `is_windows(path)` - Determines if a path is to a windows location by looking at the path separators (`/` or `\\`) will raise a `PathError` if the separators are mixed.
 * `separator(path)` - Will return the correct separator (`/` or `\\`) depending on the result of `is_path`
 * `split(path)` - Will split a path into a list of items e.g. `split('/path/to/file') -> ['path', 'to', 'file']`
 * `add_separator_to_end_of_directory(path)` - Will add the correct separator to the end of the path unless the final item is a file. This is mostly used to normalise paths to directories or as part `append_path` e.g. 
 ```
 add_separator_to_end_of_directory('/path/without/final/separator') -> '/path/without/final/separator/'
 add_separator_to_end_of_directory('/path/to/file.nxs') -> '/path/to/file.nxs'
 ```
 * `append_path(path, list_to_append)` - Will determine the correct path separator and add each item in the list to the end of the supplied path (delimited with separators). e.g.
```
 append_path('/path/', ['items', 'to', 'add']) -> '/path/items/to/add/
``` 
The purpose of the above functions is to work with the file path of operating system rather than the current operating system. This makes handling Windows paths on Unix based systems (and visa versa) much easier.


### <a name="collections">Collections</a>
Contains more autoreduction specific groups of `Path` objects.
* `InputPaths` - Paths required for reduction (data file, reduction script and reduction variables)
* `TemporaryPaths` - Paths for a temporary location to store output data. This is required to ensure that overwriting of data is handled correctly.
* `OutputPaths` - Paths for the final location where the data is to be stored (at ISIS this is on CEPH)

In addition to these, there is a `PathCollection` class that is generic and implemented by all 3 of the above. The only responsiblity of this class is to ensure that all the `Path` objects created are validated on initialisation. 
There are scenarios where you do no want to validate a `Path` object immediately (e.g. the path will be created later on or the path is not yet readable). Hence the `Path` object does not perform validation itself on initialisation.
However, we should assume that paths for autoreduction input and output already exist. 

### <a name="red-path-man">Reduction Path Manager</a>
This is designed to contain all of the `paths.collections` in one place for use in the autoreduction code base.
It is  a small wrapper class that defines `self.input_paths`, `self.temporary_paths` and `self.output_paths`.
This class encapsulates all the paths required for a single reduction run. 