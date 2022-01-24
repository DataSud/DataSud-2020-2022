# Copyright (c) 2017-2021 Neogeo-Technologies.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


from celery.utils.log import get_task_logger

from idgo_troubleshooting import celery_app
from idgo_troubleshooting.utils import get_deadlink_resource
from idgo_troubleshooting.utils import get_outdated_resource
from idgo_troubleshooting.utils import get_undocumented_resource


logger = get_task_logger(__name__)


@celery_app.task(name='idgo_troubleshooting.tasks.task_outdated_resource')
def task_outdated_resource(**kwargs):
    get_outdated_resource()


@celery_app.task(name='idgo_troubleshooting.tasks.task_undocumented_resource')
def task_undocumented_resource(**kwargs):
    get_undocumented_resource()


@celery_app.task(name='idgo_troubleshooting.tasks.task_deadlink_resource')
def task_deadlink_resource(**kwargs):
    get_deadlink_resource()
