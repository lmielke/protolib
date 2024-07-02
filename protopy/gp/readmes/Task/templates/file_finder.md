
file_finder is a feature, that should be implemented as a standalone solution. It intends to find all files in a given directory. The user should be able to limit the search using some regex like filter condition.
The files should be returned as a list of full paths.
The file_finder uses the following steps:
1. Get starting path
2. loop through all files in the directory and all subdirectories
3. get files with specified file_name
