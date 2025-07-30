# User Readme for Protolib python template package

Creates a empty **python package** using **pipenv** including all the relevant boilerpalte for a pyhon project with a single command.

Protolib itself serves as a **template** for your new package, so right after **proto clone**, you can start using the new package.

When running **proto clone** protolib is copied to your -t tgt_dir and re-structuring/re-naming is automatically done. 
NOTE: All code relevant for cloning and renaming the package is removed inside the target package. So the resulting target package cannot be used for cloning. Keep protolib if you want to create additional packages.

# Basic steps and commands
1. Clone protolib into your target directory
2. After activating protolib like 'pipenv shell' you can use the following command:
```shell
    cd .../protolib
    pipenv shell
    # minimal proto clone
    proto clone -pr 'my_superlib' -n 'my_superpackage' -a 'supi_alias' -t '/temp'
    # carefully choose your future project naming/install parameters
    # check if protolib environment is already active, and activeate if needed
    # the folowing command will create a new python package in /temp using a copy of protolib
    proto clone -pr 'my_superlib' -n 'my_superpackage' -a 'supi_alias' -t '/temp' -p 3.13 --install
    # note that by omitting the --install flag, no python environment will be created
    # clone might ask you additional questions, i.e. missing parameters
    # You can now exit proto and start coding your package
```
This will clone protolib into your new python package and install the environment using pipenv, so you can start coding right away.

When done, you can start coding your package in the newly created packag folder ('my_superpackage').
1. cd to your new package folder (i.e. '/temp/my_superlib')
2. Activate the environment using `pipenv shell`
3. To test the install sucess, run the following command:
```shell
    # retrieve some basic info about the package structure and its capabilities
    supi_alias info -i ['project', 'python'] or -v 1-3
```
Fields: 
- -i --infos Package infos [python, package] to be retreived, default: None
- -pr (project folder name),
- -n (package name), IMPORTANT NOTE: package name must be different from project folder name
- -t (target dir, where your project folder is created)
- -a (package alias) 
- -p python version [3.10, 3.11] to be used (will be set in your Pipfile)
- --install (bool) Triggers pipenv to install the environment using py_version.

<img src="https://drive.google.com/uc?id=1C8LBRduuHTgN8tWDqna_eH5lvqhTUQR4" alt="me_happy" class="plain" height="150px" width="220px">

## get and install
```shell
    git clone git@gitlab.com:larsmielke2/protopy.git ./protolib
```
## Structure
### protopy
- coding is in protolib/protopy folder, add your .py modules there
- protopy.apis contains the entry points to your package like info.py (usage: supi_alias entry_point)
- you can create as many entry points as needed 
- any entry_point.py module requires a main(*args, **kwargs) function as entry point
- __main__.py calls protolib/protopy/apis/entry_point.py[provides as shell call args]


## USAGE
### 1. Clone protopy into your target directory

### 2. Navigate to your new package and start coding
```shell 
    cd $tgt_dir
    pipenv shell
    supi_alias api_name [any args]
