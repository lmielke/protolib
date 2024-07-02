# contracts.py
import protopy.settings as sts
import protopy.gp.models.openai.model_settings as gp_sts
import os, sys
import protopy.arguments as arguments



def checks(*args, **kwargs):
    kwargs = clean_kwargs(*args, **kwargs)
    check_missing_kwargs(*args, **kwargs)
    # kwargs.update(get_model(*args, **kwargs))
    kwargs.update(adhog_chat_contracts(*args, **kwargs))
    kwargs.update(validate_regex_string(*args, **kwargs))
    check_api_available(*args, **kwargs)
    # print(f"{sts.YELLOW}kwargs: {kwargs}{sts.RESET}")
    return kwargs

def check_api_available(*args, api, **kwargs):
    apis = [os.path.splitext(p)[0] for p in os.listdir(sts.apis_dir) \
                                                if p.endswith('.py') and p != '__init__.py']
    if api not in apis:
        print(f"{sts.RED}API '{api}' not found in available apis{sts.ST_RESET}")
        print(f"{sts.YELLOW}Available APIs: {apis}{sts.ST_RESET}")
        exit()


def clean_kwargs(*args, **kwargs):
    # kwargs might come from a LLM api and might be poluted with whitespaces ect.
    cleaned_kwargs = {}
    for k, vs in kwargs.items():
        if isinstance(vs, str):
            cleaned_kwargs[k.strip()] = vs.strip().strip("'")
        else:
            cleaned_kwargs[k.strip()] = vs
    return cleaned_kwargs

def check_missing_kwargs(*args, api,  **kwargs):
    """
    Uses arguments to check if all required kwargs are provided
    """
    if api == 'clone':
        requireds = {
                        'new_pr_name': 'myhammerlib',
                        'new_pg_name': 'myhammer',
                        'new_alias': 'myham',
                        'tgt_dir': 'C:/temp',
                        }
    else:
        requireds = {}
    missings = set()
    for k, v in requireds.items():
        if k not in kwargs.keys():
            missings.add(k)
    if missings:
        print(f"{sts.RED}Missing required arguments: {missings}{sts.ST_RESET}")
        print(f"{sts.YELLOW}Required arguments are: {requireds}{sts.ST_RESET}")
        exit()

def get_model(*args, model:str, **kwargs):
    # print(f"{gp_sts.models.keys() = }")
    if model in gp_sts.models.keys():
        selected = {'model': gp_sts.models[model]}
    elif model in gp_sts.models.values():
        selected = {'model': model}
    elif model is None:
        selected = {'model': gp_sts.default_model}
    else:
        raise Exception(f"{sts.RED}Model {model} not found in gp_sts.models {sts.ST_RESET}")
    print(f"{sts.YELLOW}Model: {selected['model']}{sts.RESET}")
    return selected

def adhog_chat_contracts(*args, experts:list, **kwargs):
    if type(experts) == str:
        experts = [experts]
    else:
        pass
        # print(f"{sts.YELLOW}Contract.Experts: {experts}{sts.RESET}")
    return {'experts': experts}

def validate_regex_string(*args, api, regex, infos, **kwargs):
    if api == 'info':
        if regex is None:
            regex = f"test_{sts.package_name}"
        if infos is None:
            infos = ['user_info']
    return {'regex': regex, 'infos': infos}