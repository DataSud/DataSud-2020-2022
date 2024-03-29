# encoding: utf-8

import os
import re
import inspect
import itertools
import pkgutil

from flask import Flask, Blueprint
from flask.ctx import _AppCtxGlobals
from flask.sessions import SessionInterface

from werkzeug.exceptions import HTTPException
from werkzeug.routing import Rule


from beaker.middleware import SessionMiddleware
from paste.deploy.converters import asbool
from fanstatic import Fanstatic

from ckan.lib import helpers
from ckan.lib import jinja_extensions
from ckan.common import config, g
import ckan.lib.app_globals as app_globals
from ckan.plugins import PluginImplementations
from ckan.plugins.interfaces import IBlueprint, IMiddleware
from ckan.views import (identify_user,
                        set_cors_headers_for_response,
                        check_session_cookie,
                        )


import logging
log = logging.getLogger(__name__)


def make_flask_stack(conf, **app_conf):
    """ This has to pass the flask app through all the same middleware that
    Pylons used """

    root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    debug = asbool(app_conf.get('debug', app_conf.get('DEBUG', False)))
    testing = asbool(app_conf.get('testing', app_conf.get('TESTING', False)))

    app = flask_app = CKANFlask(__name__)
    app.debug = debug
    app.testing = testing
    app.template_folder = os.path.join(root, 'templates')
    app.app_ctx_globals_class = CKAN_AppCtxGlobals
    app.url_rule_class = CKAN_Rule

    # Update Flask config with the CKAN values. We use the common config
    # object as values might have been modified on `load_environment`
    if config:
        app.config.update(config)
    else:
        app.config.update(conf)
        app.config.update(app_conf)

    # Do all the Flask-specific stuff before adding other middlewares

    # Secret key needed for flask-debug-toolbar and sessions
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = config.get('beaker.session.secret')
    if not app.config.get('SECRET_KEY'):
        raise RuntimeError(u'You must provide a value for the secret key'
                           ' with the SECRET_KEY config option')

    if debug:
        from flask_debugtoolbar import DebugToolbarExtension
        app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
        DebugToolbarExtension(app)

    # Use Beaker as the Flask session interface
    class BeakerSessionInterface(SessionInterface):
        def open_session(self, app, request):
            if 'beaker.session' in request.environ:
                return request.environ['beaker.session']

        def save_session(self, app, session, response):
            session.save()

    namespace = 'beaker.session.'
    session_opts = dict([(k.replace('beaker.', ''), v)
                        for k, v in config.iteritems()
                        if k.startswith(namespace)])
    if (not session_opts.get('session.data_dir') and
            session_opts.get('session.type', 'file') == 'file'):
        cache_dir = app_conf.get('cache_dir') or app_conf.get('cache.dir')
        session_opts['session.data_dir'] = '{data_dir}/sessions'.format(
                data_dir=cache_dir)

    app.wsgi_app = SessionMiddleware(app.wsgi_app, session_opts)
    app.session_interface = BeakerSessionInterface()

    # Add Jinja2 extensions and filters
    extensions = [
        'jinja2.ext.do', 'jinja2.ext.with_',
        jinja_extensions.SnippetExtension,
        jinja_extensions.CkanExtend,
        jinja_extensions.CkanInternationalizationExtension,
        jinja_extensions.LinkForExtension,
        jinja_extensions.ResourceExtension,
        jinja_extensions.UrlForStaticExtension,
        jinja_extensions.UrlForExtension
    ]
    for extension in extensions:
        app.jinja_env.add_extension(extension)
    app.jinja_env.filters['empty_and_escape'] = \
        jinja_extensions.empty_and_escape

    # Common handlers for all requests
    app.before_request(ckan_before_request)
    app.after_request(ckan_after_request)

    # Template context processors
    app.context_processor(helper_functions)
    app.context_processor(c_object)

    @app.route('/hello', methods=['GET'])
    def hello_world():
        return 'Hello World, this is served by Flask'

    @app.route('/hello', methods=['POST'])
    def hello_world_post():
        return 'Hello World, this was posted to Flask'

    # Auto-register all blueprints defined in the `views` folder
    _register_core_blueprints(app)

    # Set up each IBlueprint extension as a Flask Blueprint
    for plugin in PluginImplementations(IBlueprint):
        if hasattr(plugin, 'get_blueprint'):
            plugin_blueprints = plugin.get_blueprint()
            if not isinstance(plugin_blueprints, list):
                plugin_blueprints = [plugin_blueprints]
            for blueprint in plugin_blueprints:
                app.register_extension_blueprint(blueprint)

    # Start other middleware

    for plugin in PluginImplementations(IMiddleware):
        app = plugin.make_middleware(app, config)

    # Fanstatic
    if debug:
        fanstatic_config = {
            'versioning': True,
            'recompute_hashes': True,
            'minified': False,
            'bottom': True,
            'bundle': False,
        }
    else:
        fanstatic_config = {
            'versioning': True,
            'recompute_hashes': False,
            'minified': True,
            'bottom': True,
            'bundle': True,
        }
    root_path = config.get('ckan.root_path', None)
    if root_path:
        root_path = re.sub('/{{LANG}}', '', root_path)
        fanstatic_config['base_url'] = root_path
    app = Fanstatic(app, **fanstatic_config)

    for plugin in PluginImplementations(IMiddleware):
        try:
            app = plugin.make_error_log_middleware(app, config)
        except AttributeError:
            log.critical('Middleware class {0} is missing the method'
                         'make_error_log_middleware.'
                         .format(plugin.__class__.__name__))

    # Update the main CKAN config object with the Flask specific keys
    # that were set here or autogenerated
    flask_config_keys = set(flask_app.config.keys()) - set(config.keys())
    for key in flask_config_keys:
        config[key] = flask_app.config[key]

    # Add a reference to the actual Flask app so it's easier to access
    app._wsgi_app = flask_app

    return app


def ckan_before_request():
    u'''Common handler executed before all Flask requests'''

    # Update app_globals
    app_globals.app_globals._check_uptodate()

    # Identify the user from the repoze cookie or the API header
    # Sets g.user and g.userobj
    identify_user()


def ckan_after_request(response):
    u'''Common handler executed after all Flask requests'''

    # Check session cookie
    response = check_session_cookie(response)

    # Set CORS headers if necessary
    response = set_cors_headers_for_response(response)

    # Default to cache-control private if it was not set
    if response.cache_control.private is None:
        response.cache_control.private = True

    return response


def helper_functions():
    u'''Make helper functions (`h`) available to Flask templates'''
    if not helpers.helper_functions:
        helpers.load_plugin_helpers()
    return dict(h=helpers.helper_functions)


def c_object():
    u'''
    Expose `c` as an alias of `g` in templates for backwards compatibility
    '''
    return dict(c=g)


class CKAN_Rule(Rule):

    u'''Custom Flask url_rule_class.

    We use it to be able to flag routes defined in extensions as such
    '''

    def __init__(self, *args, **kwargs):
        self.ckan_core = True
        super(CKAN_Rule, self).__init__(*args, **kwargs)


class CKAN_AppCtxGlobals(_AppCtxGlobals):

    '''Custom Flask AppCtxGlobal class (flask.g).'''

    def __getattr__(self, name):
        '''
        If flask.g doesn't have attribute `name`, fall back to CKAN's
        app_globals object.
        If the key is also not found in there, an AttributeError will be raised
        '''
        return getattr(app_globals.app_globals, name)


class CKANFlask(Flask):

    '''Extend the Flask class with a special method called on incoming
     requests by AskAppDispatcherMiddleware.
    '''

    app_name = 'flask_app'

    def can_handle_request(self, environ):
        '''
        Decides whether it can handle a request with the Flask app by
        matching the request environ against the route mapper

        Returns (True, 'flask_app', origin) if this is the case.

        `origin` can be either 'core' or 'extension' depending on where
        the route was defined.
        '''

        urls = self.url_map.bind_to_environ(environ)
        try:
            rule, args = urls.match(return_rule=True)
            origin = 'core'
            if hasattr(rule, 'ckan_core') and not rule.ckan_core:
                origin = 'extension'
            log.debug('Flask route match, endpoint: {0}, args: {1}, '
                      'origin: {2}'.format(rule.endpoint, args, origin))
            return (True, self.app_name, origin)
        except HTTPException:
            return (False, self.app_name)

    def register_extension_blueprint(self, blueprint, **kwargs):
        '''
        This method should be used to register blueprints that come from
        extensions, so there's an opportunity to add extension-specific
        options.

        Sets the rule property `ckan_core` to False, to indicate that the rule
        applies to an extension route.
        '''
        self.register_blueprint(blueprint, **kwargs)

        # Get the new blueprint rules
        bp_rules = itertools.chain.from_iterable(
            v for k, v in self.url_map._rules_by_endpoint.iteritems()
            if k.startswith(u'{0}.'.format(blueprint.name))
        )

        # This compare key will ensure the rule will be near the top.
        top_compare_key = False, -100, [(-2, 0)]
        for r in bp_rules:
            r.ckan_core = False
            r.match_compare_key = lambda: top_compare_key


def _register_core_blueprints(app):
    u'''Register all blueprints defined in the `views` folder
    '''
    def is_blueprint(mm):
        return isinstance(mm, Blueprint)

    for loader, name, _ in pkgutil.iter_modules(['ckan/views'], 'ckan.views.'):
        module = loader.find_module(name).load_module(name)
        for blueprint in inspect.getmembers(module, is_blueprint):
            app.register_blueprint(blueprint[1])
            log.debug(u'Registered core blueprint: {0!r}'.format(blueprint[0]))
