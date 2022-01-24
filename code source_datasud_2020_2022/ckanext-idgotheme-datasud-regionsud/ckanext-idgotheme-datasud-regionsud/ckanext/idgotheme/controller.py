# coding: utf-8


from ckan.common import config
import ckan.lib.base as base
import ckan.plugins.toolkit as toolkit
import requests
from urlparse import urlparse
import re


class ExportController(base.BaseController):

    def query_export(self, *args, **kwargs):
        args = dict(kwargs['environ']['paste.parsed_dict_querystring'][0])

        http_referer = kwargs['environ'].get('HTTP_REFERER', None)
        if http_referer:
            referer = urlparse(http_referer)
            found = re.search(r'^\/(\w+)\/(.+)$', referer.path)
            if found and len(found.groups()) == 2:
                key = {'group': 'groups'}.get(found.groups()[0], found.groups()[0])
                value = found.groups()[1]
                args[key] = value

        facet_filters = [
            'organization',
            'groups',
            'datatype',
            'res_format',
            'support',
            'license_id',
            'tags',
            'frequency',
            'granularity',
        ]

        q = ''
        fq = ''
        bbox = ''
        resformat = 'odl'

        for key in args:
            if key == 'resformat':
                resformat = args[key]
            elif key == 'ext_bbox':
                bbox = args[key]
            elif key == 'q':
                q = args[key]
            else:
                if key in facet_filters:
                    fq += ' +' + key + ':' + args[key].decode('utf-8')

        context = {
            'model': base.model,
            'session': base.model.Session,
            'user': base.c.user,
        }

        data_dict = {'rows': 100000, 'q': q, 'fq': fq, 'ext_bbox': bbox}

        search_result = toolkit.get_action('package_search')(context, data_dict)
        results = [x['id'] for x in search_result.get('results', [])]

        # POST REQUEST
        export_url = config.get('ckanext.idgotheme.url_site_publier', '') + '/dataset/export?'
        export_data = {'ids': ','.join(results), 'format': resformat}
        return requests.post(url=export_url, data=export_data)
