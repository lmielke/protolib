import io, json, jinja2, os, re, time
from typing import Dict, Any, List, Union

import protopy.settings as sts
import protopy.helpers.collections as hlp
from protopy.apis.info import main as info_main
from protopy.gp.data.vectorize import VectorData
import inspect

class Template:
    """
    A class to process and save Jinja2 templates.

    Attributes:
        template_dir (str): The directory to the template files.
        experts_template_path (str): The path where the processed file will be saved.
    """
    templ_infos = {}
    # we need to pass the class name to info_main
    default_info = info_main(f"{inspect.stack()[0][3]}.default_info", verbose=0)


    def __init__(self, owner, *args, t_name: str, **kwargs) -> None:
        """
        Initialize the Template object with paths.

        Args:
            t_name (str): The name of the template file.
                            For expert its generally the expert´s domain.md
            t_path (str): The type of template to use. [task, expert]
        """
        self.owner = owner
        self.t_name = t_name if t_name.endswith('.md') else f'{t_name}.md' if t_name else ''
        self.t_path = self.get_template_path(owner, *args, **kwargs)
        self.entry_point, self.target_path = self.get_entry_point(*args, **kwargs)
        self.initialized = False

    def get_template_path(self, owner:object, *args, **kwargs):
        templ_dir_name = type(owner).__name__
        templ_path = os.path.join(sts.readme_dir, templ_dir_name, 'templates')
        for _dir, dirs, files in os.walk(templ_path):
            if self.t_name in files:
                return os.path.join(_dir, self.t_name)
        return os.path.join(templ_path, 'main.md')

    def get_entry_point(self, *args, **kwargs) -> (str, str):
        """
        Get the paths for the template and the target file.

        Args:
            t_path (str): The type of template to use. [task, expert]

        Returns:
            Dict[str, str]: The paths for the template and the target file.
        """
        rd_dir, rd_name = os.path.split(self.t_path)
        # entry_point is the starting template from where the rendering starts
        entry_point = os.path.join(rd_dir, f"main.md")
        target_path = os.path.join(os.path.dirname(rd_dir), self.t_name)
        return entry_point, target_path

    def add_context(self, context:dict, *args, **kwargs):
        kwargs.update(context)
        kwargs.update(self.__dict__)
        kwargs.update({'owner': f"{self.owner.__class__.__name__}"})
        # sometimes only the main template must be loaded without any sub-templates
        if kwargs.get('t_path') == kwargs.get('entry_point'):
            kwargs['t_path'] = ''
        return kwargs


    def get_sys_infos(self, *args, 
                                infos: Union[List[str], str] = None, 
                                tgt_dir: str = None, 
                                verbose: int = 0, 
                                **kwargs
        ) -> str:
        """
        Retrieve system information, checking class-level templ_infos first and then getting 
        missing ones from info_main.

        Args:
            infos (Union[List[str], str]): The information to retrieve.
            verbose (int, optional): The verbosity level.

        Returns:
            str: The retrieved system information.
        """
        if not infos and not tgt_dir:
            return ''
        elif isinstance(infos, str):
            infos = [infos]
        elif infos is None:
            infos = []
        # Check for infos already available in templ_infos
        missing_infos = [info for info in infos if info not in self.templ_infos]
        for i, missing in enumerate(missing_infos):
            # Retrieve missing infos from info_main
            new_info = info_main(*args, infos=[missing], verbose=0, init=True, **kwargs)
            # Update the class-level templ_infos with the newly retrieved infos
            self.templ_infos.update({missing: new_info})
        # Return the requested infos from templ_infos
        info_out = '\n'.join([self.templ_infos[info] for info in infos])
        info_out += self.default_info
        info_out += info_main(*args, tgt_dir=tgt_dir, verbose=0, init=True, **kwargs)
        return info_out

    def get_all_infos(self, *args, verbose:int=3, **kwargs) -> str:
        return info_main(*args, infos=None, verbose=verbose, **kwargs)

    def load_instructs(self, template_path:str, *args, **kwargs) -> str:
        """
        Load the instructs for the expert.

        Returns:
            str: The instructs for the expert.
        """
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                return f.read()
        else:
            return None

    def load_task(self, *args, **kwargs) -> str:
        """
        Load the task description.

        Returns:
            str: The task description.
        """
        if os.path.exists(self.task_path):
            with open(self.task_path, 'r') as f:
                return f.read()
        else:
            return None

    def render_template(self, *args, **kwargs) -> str:
        """
        Generate output from the template using the provided context.

        Args:
            t_path (str): The type of template to use. [task, expert]

        Returns:
            str: The rendered template.
        """
        template = (jinja2.Environment(
                        loader=jinja2.FileSystemLoader([os.path.dirname(self.t_path)]))
                            .get_template(os.path.basename(self.entry_point))
                    )
        # context = self.create_context(self.t_path, *args, t_path=t_path, **kwargs)
        try:
            rendered = template.render(context=self.add_context(*args, **kwargs))
        except jinja2.exceptions.TemplateNotFound as e:
            rendered = f"{sts.RED}render_template Not found: {e}{sts.RESET}\n<< infos >>"
        return rendered

    def load(self, *args, **kwargs):
        """
        Takes the render_template results, adds infos and formats to the instructs
        """
        rendered = self.render_template(*args, **kwargs)
        infos = self.get_sys_infos(*args, **kwargs)
        rendered = self._add_infos_to_rendered(rendered, infos, *args, **kwargs)
        return rendered

    def _add_infos_to_rendered(self, text, r_text, *args, pos='<< infos >>', **kwargs):
        oc_nbr = text.count(pos)
        if oc_nbr > 1:
            text = text.replace(pos, '', oc_nbr - 1)
            text = text.replace(pos, r_text)
        elif oc_nbr == 1:
            text = text.replace(pos, r_text)
        elif oc_nbr == 0:
            text = f"{text}\n{r_text}"
        return text

    def render_and_save(self, *args, **kwargs) -> None:
        """
        Render the template with the given context and save the output.

        Args:
            context (Dict[str, Any]): The context variables for rendering the template.
        """
        instructs = self.render_template(*args, **kwargs)
        with open(self.target_path, 'w', encoding='utf-8') as f:
            f.write(instructs)
        return instructs
