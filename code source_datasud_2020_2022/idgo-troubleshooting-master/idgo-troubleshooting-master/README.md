# Idgo Troubleshooting

Idgo Troubleshooting is an application that allows users to analyze CKAN datas through an administration panel.
In this version, it identifies:
- resources whose planned update has expired
- undocumented datasets (with no resources)
- resources for which an external link is broken


## License and contributors

Idgo-Troubleshooting is mainly developed by Neogeo Technologies under the following license:
Apache License 2.0
http://www.apache.org/licenses/LICENSE-2.0

---

## TABLE OF CONTENTS
 - [TABLE OF CONTENTS](#TABLE-OF-CONTENTS)
 - [Installation](#Installation)
   - [Prerequisites](#Prerequisites)
   - [Creation of Django project and clone](#Creation-of-Django-project-and-clone)
 - [Configuration](#Configuration)
   - [Edition of settings.py and urls.py](#Edition-of-settings.py-and-urls.py)

---

## Installation

### Prerequisites

Python 3.x

### Creation of Django project and clone

```shell
# Creation and activation of the virtual environment
python3.5 -m venv geocontrib_venv/
source geocontrib_venv/bin/activate

# Clone of the project
git clone https://git.neogeo.fr/idgo/apps/idgo-troubleshooting.git idgo-troubleshooting/

# Installation of dependencies
pip install --upgrade pip
pip install -r src/requirements.txt

# Creation of a Django project
django-admin startproject config .
```

## Configuration

### Edition of settings.py

For development, copy the content of idgo_troubleshooting/config_sample/settings.py into config/settings.py.
Type your username under 'DATABASES'

In production, only CKAN\_URL must be filled in the settings.py

### Editer les Tâches périodiques

Dans l'interface d'administration de Django, ajouter 3 tâches périodiques :
* idgo_troubleshooting.tasks.task_undocumented_resource
* idgo_troubleshooting.tasks.task_outdated_resource
* idgo_troubleshooting.tasks.task_deadlink_resource


De préférence 1 fois par jour.
Penser à mettre une date de début pour éviter les problèmes de logs.
Penser à activer la tâche périodique.

Le worker Celery utilisé est celui de Django (namespace CELERY).
Inutile d'en rajouté un.
 
