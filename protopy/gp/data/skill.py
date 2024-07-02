"""
skill.py
This module contains the Skill class which is used to define a skill
with its name, description, standards, and instructions.
"""

from dataclasses import dataclass, field
from typing import Optional

# Assuming the correct imports for Template and settings as in your original example
from protopy.gp.data.retrievals import Template
import protopy.settings as sts

@dataclass
class Skill:
    name: str
    description: Optional[str] = None
    standards: Optional[str] = None
    instructs: Optional[str] = ""

    def __post_init__(self, *args, **kwargs) -> None:
        """
        Initialize the Skill object with instructions.

        Args:
            *args, **kwargs: Additional arguments and keyword arguments for template loading.
        """
        self.instructs = self.load_instructions(*args, **kwargs)

    def to_dict(self) -> dict:
        """
        Convert the Skill dataclass to a dictionary, combining description and standards.

        Returns:
            dict: A dictionary representation of the skill where the skill name is a key to its details.
        """
        return {
                'name': self.name,
                'description': self.description, 
                'standards': self.standards,
            }

    def load_instructions(self, *args, instructs:str='', **kwargs):
        """
        Every skill requires a different set of instructions. 
        This function reads the instructions for the skill and applies them using a given template.

        Args:
            *args, **kwargs: Additional arguments and keyword arguments for template loading.

        Returns:
            str: Updated instructions with added context from the template.
        """
        # Instantiate the Template with necessary parameters. Note adjustment for template name (t_name)
        template = Template(self, *args, t_name=self.name, **kwargs)

        # Adds skill-specific context to the template context
        instructs += '\n'
        instructs += template.load(self.to_dict(), *args, infos=None, **kwargs)
        return instructs
