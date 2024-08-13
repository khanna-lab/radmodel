# radmodel
Repository for code related to radx-up r21 modeling


## Installation

1. Create virtual environment - `python3 -m venv ~/.venvs/radmodel-py3.11`. Replace `~/.venvs` with wherever you keep your virtual environments, and py3.11 with whatever python version you are using.
2. Activate the virtual environment - e.g., `source ~/.venvs/radmodel-py3.11/bin/activate`
3. Install repast4py - https://repast.github.io/repast4py.site/guide/user_guide.html#_requirements
3. cd into radmodel repo directory - `pip install -e .`

By install with `-e` any changes you make to the radmodel code will be reflected in the
virtual environment install.

## Testing and Running

1. Activate your radmodel virtual environment
2. Run with `radmodel`

```
❯ radmodel -h
usage: radmodel [-h] parameters_file [parameters]

positional arguments:
  parameters_file  parameters file (yaml format)
  parameters       json parameters string

options:
  -h, --help       show this help message and exit

❯ radmodel params/radmodel_params.yaml 
{'stop.at': 672.1}
```

3. Test with `pytest`

```
❯ pytest
================================== test session starts ===================================
platform linux -- Python 3.11.9, pytest-8.3.2, pluggy-1.5.0
rootdir: /home/nick/Documents/repos/radmodel
configfile: pyproject.toml
collected 3 items                                                                        

tests/test_core.py ...                                                             [100%]

=================================== 3 passed in 0.06s ====================================
```

## Funding Information
[R21 MD 019388](https://reporter.nih.gov/search/3xP1HNXGDkKYlxiG9LbyJA/project-details/10933019)  
