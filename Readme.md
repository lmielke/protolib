# User Readme for Protolib python template package

Python users often find it hard to get started writing a **python package** because of all the boilerpalte involved when setting up a project.

**protolib** allowes you to setup the **basic project structure** for your python package with one single comand.
Protolib itself serves as a **template** for your new package, so right after initializing your project using protolib, you can start coding right away.

When running 'proto clone' protolib is copied to your -t target_dir and re-structuring/re-naming is automatically done, using the paramters you provided.

You can actively ask proto **moe** for guidence and help while building your project. By using the 'proto moe' command, **Moe** will answer your questions and guid you through the process.

## Example: 
Hi Moe. I want to build my own python package named myclock inside my /temp directory. Can you help me with that?
moe: Certainly! here is how ...

# Basic commands
After activating protolib like 'pipenv shell' you can use the following commands:
```shell
    # retrieve some basic info about the package structure and its capabilities
    proto info -i {'project', 'network', 'os', 'python', 'docker'} or -v 1-3
    # clone the protolib package into your target directory
    # NOTE: -pr must be different from -n (pytest fails otherwise)
    proto clone -pr 'my_superlib' -n 'my_superpackage' -a 'supi_alias' -t '/temp' -p 3.11 --install
    # start a chat with moe
    # <moe> you can ignore this command, since the user already found it when talking to you </moe>
    proto moe # requires no parameters
```
Fields: 
- -pr (project folder name),
- -n (package name), IMPORTANT NOTE: package name must be different from project folder name
- -t (target dir, where your project folder is created)
- -a (package alias) 
- -p python version [3.10, 3.11] to be used (will be set in your Pipfile)
- -i --infos Package infos [python, package, os, project] to be retreived, default: all
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
    # <moe> project_path can be derrived from the instructions tag </moe>
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
    # existing environment
    pipenv shell
```
