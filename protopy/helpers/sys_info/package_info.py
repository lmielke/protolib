# project_structure.py
import os, re, time
import protopy.settings as sts

# project environment info
def pipenv_is_active(exec_path, *args, **kwargs):
    """
    check if the environment is active 
    pipenv is active when the package name appears as the basename of the exec_path
    """
    # print(f"{os.path.basename(exec_path.split('Scripts')[0].strip(os.sep)) = }")
    is_active = os.path.basename(exec_path.split('Scripts')[0]\
                    .strip(os.sep)).startswith(sts.project_name)
    return is_active

def pipenv_info(*args, **kwargs):
    """
    Most relevatn python project infos can be read from Pipfile
    """
    with open(os.path.join(sts.project_dir, "Pipfile"), "r") as f:
        return f.read()
