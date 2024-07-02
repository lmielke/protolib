"""
Handles RAG (Retrieval Augmented Generation) data for the agents.
"""


import io, json, os, re
from typing import Dict, Any, List, Union

import protopy.settings as sts
import protopy.helpers.collections as hlp

class VectorData:
    pass