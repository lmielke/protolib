# settings.py
import os, re, sys, time, yaml
from datetime import datetime as dt

package_name = "protopy"
package_dir = os.path.dirname(__file__)
project_dir = os.path.dirname(package_dir)
project_name = os.path.basename(project_dir)

apis_dir = os.path.join(package_dir, "apis")
apis_json_dir = os.path.join(package_dir, "apis", "json_schemas")
# gp related paths
gp_logs = os.path.join(package_dir, 'gp', 'logs')
chat_logs_dir = os.path.join(gp_logs, 'chat_logs')
chat_hist_dir = os.path.join(gp_logs, 'chat_hist')
info_logs_dir = os.path.join(gp_logs, 'info_logs')
resources_dir = os.path.join(package_dir, "resources")
secrets_dir = os.path.dirname(os.environ.get('secrets'))

instructions_file = lambda expert: os.path.join(resources_dir, f"Readme_{expert}.md")

test_dir = os.path.join(package_dir, "test")
test_data_dir = os.path.join(test_dir, "data")

# color settings
import colorama
# colors to be used everywhere
YELLOW = colorama.Fore.YELLOW
GREEN = colorama.Fore.GREEN
RED = colorama.Fore.RED
MAGENTA = colorama.Fore.MAGENTA
BLUE = colorama.Fore.BLUE
CYAN = colorama.Fore.CYAN
WHITE = colorama.Fore.WHITE
# additional color options
DIM = colorama.Style.DIM
# setting back to normal
RESET = colorama.Fore.RESET
ST_RESET = colorama.Style.RESET_ALL

colors = {
            'YELLOW': YELLOW,
            'GREEN': GREEN,
            'MAGENTA': MAGENTA,
            'BLUE': BLUE,
            'CYAN': CYAN,
            'WHITE': WHITE,
            'RED': RED,
         }

colors_in_use = {}
default_color, sudo_color, user_color = 'RED', 'RED', 'YELLOW'
sudo_color_code, user_color_code = RED, YELLOW
colors_available = set(colors.keys())
# RED is reserved for admin, so can not be used by any other expert
colors_available.remove(sudo_color.upper())
colors_available.remove(user_color.upper())
# content formatting
code_color = CYAN
language_color = BLUE
# expert settings
experts, in_chat = {}, set()
sudo = 'admin'
session_id = f"{re.sub(r'([: .])', r'-' , str(dt.now()))}"
# due to available colors, the number of experts is limited to 7
max_experts = len(colors_available) + 5

# openaiFunction = '@OpenAi.function'.lower()
open_ai_func_prefix = 'open_ai_api_'
json_ext = '.json'

time_stamp = lambda: re.sub(r"([: .])", r"-" , str(dt.now()))
session_time_stamp = time_stamp()

ignore_dirs = {
                ".git",
                "build",
                "gp",
                "dist",
                "models",
                "*.egg-info",
                "__pycache__",
                ".pytest_cache",    
                ".tox",
}
abrev_dirs = {
                "log",
                "logs",
                "testopia_logs",
                "chat_logs",
}

tags = {
    "general": ["<general_info>", "</general_info>", BLUE],
    "chat": ["<chat_info>", "</chat_info>", BLUE],
    "expert": ["<expert_info>", "</expert_info>", BLUE],
    "instructs": ["<INST>", "</INST>", CYAN],
    "package": ["<package_info>", "</package_info>", BLUE],
    "system": ["<system_info>", "</system_info>", CYAN],
    "project": ["<project_info>", "</project_info>", BLUE],
    "network": ["<network_info>", "</network_info>", CYAN],
    "python": ["<python_info>", "</python_info>", BLUE],
    "docker": ["<docker_info>", "</docker_info>", CYAN],
    "unittest": ["<unittest_info>", "</unittest_info>", BLUE],
}

roles = {'assistant': MAGENTA, 'user': GREEN, 'system': YELLOW, 'unittest': CYAN, }
# experts = {'sherlock': CYAN, 'moe': YELLOW, 'mr_robot': BLUE, 'you': GREEN, 
            # 'alice': BLUE, 'bob': CYAN}
watermark, exec_watermark = f"{WHITE}►{RESET}", f"{YELLOW}►{RESET}"
# instructions
readme_dir = os.path.join(package_dir, 'gp', 'readmes')
instruct_path = lambda expert_name: os.path.join(readme_dir, f"{expert_name}.md")

# Task settings
assembly_ixs = {0: 'low', 1: 'medium', 2: 'moderate', 4: 'high',}
# skills = {
#             'admin': {'domain':'admin', 'infos': ['network', 'system', 'project', 'docker', 'python']}, 
#             'lars_m': {'domain':'admin', 'infos': ['network', 'system', 'project', 'docker', 'python']}, 
#             'demarco_t': {'domain':'management', 'infos': ['project', 'ps_history', 'os_activity']}, 
#             'poppendieck_m': {'domain':'system', 'infos': ['network', 'system', 'ps_history'],}, 
#             'springmeyer_d': {'domain':'programmer', 'infos': ['python'],}, 
#             'richards_m': {'domain':'architect', 'infos': ['project', 'docker'],}, 
#             'default': {'domain':'programmer', 'infos': ['python'],}, 
#             }

default_expert = 'User'
skills = {
    'admin': {
        'domain': 'admin', 
        'default_model': 'l3_1',
        'know_how': ['network', 'os', 'project', 'kernel', 'communication'], 
        'info': ['network', 'project', 'os', 'docker', 'os_activity']
    },
    'User': {
        'domain': 'programmer', 
        'default_model': 'l3_1',
        'know_how': ['Linux', 'project', 'open_source', 'man-month', 'system'], 
        'info': ['ps_history', 'python', 'os', 'project', 'os_activity']
    },
    'deluca_j': {
        'domain': 'development',
        'default_model': 'l3_1',
        'know_how': ['FDD', 'software development', 'agile', 'project management'],
        'info': ['project', 'os', 'network', 'ps_history']
    }, # Jeff De Luca,
    'lattner_c': {
        'domain': 'programmer', 
        'default_model': 'l3_1',
        'know_how': ['compilers', 'LLVM', 'Swift'], 
        'info': ['project', 'os', 'python', 'docker']
    },  # Chris Lattner
    'springmeyer_d': {
        'domain': 'python_programmer', 
        'default_model': 'l3_1',
        'know_how': ['python'], 
        'info': ['python', 'docker', 'project']
    },  # Dane Springmeyer
    'torvalds_l': {
        'domain': 'system_linux', 
        'default_model': 'l3_1',
        'know_how': ['Linux', 'kernel', 'open_source'], 
        'info': ['os_activity', 'os', 'network']
    },  # Linus Torvalds
    'hanselman_s': {
        'domain': 'system_windows',
        'default_model': 'l3_1',
        'know_how': ['Windows', 'Linux', 'PowerShell', 'Bash'],
        'info': ['os_activity', 'os', 'network', 'project']
    },  # Scott Hanselman
    'farley_d': {
        'domain': 'devops', 
        'default_model': 'l3_1',
        'know_how': ['continuous_delivery', 'automation', 'CI/CD'], 
        'info': ['docker', 'os', 'os_activity', 'project']
    },  # Dave Farley
    'demarco_t': {
        'domain': 'management', 
        'default_model': 'l3_1',
        'know_how': ['project', 'man-month', 'communication'], 
        'info': ['project', 'os', 'os_activity']
    },  # Tom DeMarco
    'fowler_m': {
        'domain': 'architect',
        'default_model': 'l3_1',
        'know_how': ['software architecture', 'design patterns', 'microservices', 'agile'],
        'info': ['project', 'os', 'network', 'docker']
    } ,  # Martin Fowler
    'kim_g': {
        'domain': 'devops', 
        'default_model': 'l3_1',
        'know_how': ['automation', 'infrastructure', 'CI/CD', 'monitoring'], 
        'info': ['docker', 'os', 'os_activity', 'network']
    },  # Gene Kim
    'poppendieck_m': {
        'domain': 'system_process', 
        'default_model': 'l3_1',
        'know_how': ['lean', 'agile', 'process', 'efficiency'], 
        'info': ['project', 'os', 'os_activity']
    },  # Mary Poppendieck
}

# these values are used to controll the text lenght depending on verbosity
table_width, inner_width = 80, 70
visible_lines = 3
visible_chars = table_width * visible_lines
ansi_replaces = {
    'â–¼': '▼',
    'â–': '–',
    'â–“': '–',
    '\n': '\n',
    # Add more replacements as needed
}
code_regex = re.compile(r'```(\w*)(.*?)```', re.DOTALL)


split_flags = r'(\.\n|\d+\.\s|\|[-.].*|[|]\s{1,2}[0-9 ]{1,2}\s{1,2}[|].*|[+|]----[+].*|-\s|#+\s.+|\nd-+\s|<code_block_\d+>|<instructions>|#########)'
hierarchy_empties = r'\x1b\[\d\dm|\x1b\[\dm\x1b\[\d\dm'

# state cache settings
cache_state_dir = os.path.join(package_dir, r"helpers")
cache_state_name = 'state.yaml'
# Define the default maximum cache hours
max_cache_hours = 20

file_types = {
                '.py': 'python',
                '.pyw': 'python',
                '.md': 'markdown',
                '.ps1': 'powershell',

}