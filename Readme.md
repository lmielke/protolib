# User Readme for Protolib python template package

Creates a empty **python package** including all the relevant boilerpalte for a pyhon project with a single command.

Protolib itself serves as a **template** for your new package, so right after initializing your project using protolib, you can start coding right away.

When running 'proto clone' protolib is copied to your -t target_dir and re-structuring/re-naming is automatically done, using the paramters you provided. NOTE: all the code relevant for cloning the package is removed for the target package.

# Basic commands
After activating protolib like 'pipenv shell' you can use the following commands:
```shell
    # retrieve some basic info about the package structure and its capabilities
    proto info -i {'project', 'python',} or -v 1-3
    # clone the protolib package into your target directory
    # NOTE: -pr must be different from -n (pytest fails otherwise)
    proto clone -pr 'my_superlib' -n 'my_superpackage' -a 'supi_alias' -t '/temp' -p 3.13 --install
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
- coding is in protolib/protopy folder, add your .py files there
- __main__.py calls protolib/protopy/apis/some_api.py[provides as shell call args]

## USAGE
### 1. Clone protopy into your target directory
```shell
    # NOTE: $protolib is the path to the protolib package.
    cd project_path
    # carefully choose your future project naming/install parameters
    # check if environment is already active, and activeate if needed
    # run 'pipenv shell' folowed by 'proto clone'or run 'pipenv run proto clone' directly
    # the folowing command will create a new python package in /temp using a copy of protolib
    pipenv run proto clone -pr 'my_superlib' -n 'my_superpackage' -a 'supi_alias' -t '/temp' -p 3.11 --install
    # note that by omitting the --install flag, no python environment will be created
    # minimal proto clone
    pipenv run proto clone -pr 'my_superlib' -n 'my_superpackage' -a 'supi_alias' -t '/temp'
    # clone might ask you additional questions, i.e. missing parameters
    # You can now exit proto and start coding your package
```

### 2. Navigate to your new package and start coding
```shell 
    cd $target_dir
    # if you did run 'proto clone' using the --install flag you can now activate your
    # otherwise you use pipenv install to create the environment
    # existing environment
    pipenv shell
```
