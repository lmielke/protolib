# User Readme for Protolib package

## Protolib Description
Protolib ...

## How to run Protolib
1. cd to your new package folder (i.e. '(/.../protolib)')
2. Activate the environment using `pipenv shell`
3. To test the install sucess, run the following command:
```shell
    # retrieve some basic info about the package structure and its capabilities
    proto info -i ['project', 'python'] or -v 1-3
```
Fields: 
- -i --infos Package infos [python, package] to be retreived, default: None
- -v --verbose Verbosity level, default: 1 (1-3)

<img src="https://drive.google.com/uc?id=1C8LBRduuHTgN8tWDqna_eH5lvqhTUQR4" alt="me_happy" class="plain" height="150px" width="220px">

## get and install
```shell
    git clone git@gitlab.com:username/protopy.git ./protolib
```
## Structure
### protopy
- coding is in protolib/protopy folder, add your .py modules there
- protopy.apis contains the entry points to your package like info.py (usage: proto entry_point)
- you can create as many entry points as needed 
- any entry_point.py module requires a main(*args, **kwargs) function as entry point
- __main__.py calls protolib/protopy/apis/entry_point.py[provides as shell call args]


## USAGE
### 1. Clone protopy into your target directory

### 2. Navigate to your new package and start coding
```shell 
    cd $tgt_dir
    pipenv shell
    proto api_name [any args]
