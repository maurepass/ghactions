# encoding: utf-8
from __future__ import with_statement

import functools
import os

from fabric.api import cd, env, run, settings
from fabric.colors import green, red, yellow
from fabric.context_managers import warn_only
from fabric.contrib.files import exists
from fabric.decorators import runs_once, with_settings
from fabric.operations import local
from unipath import Path

LIB_DIR_PATH = Path(os.path.abspath(__file__)).parent.parent


def get_django_version():
    try:
        import django
        major, minior, _ = django.VERSION[:3]
        return major, minior
    except ImportError:
        print(red("Cannot determine django version. Is it installed in your virtualenv?"))
        return 0, 0


def roles(*roles):
    """ Make a function run only on hosts that have certain roles.

        Fixes fabric limitation, see:
        http://nedbatchelder.com/blog/201201/decorated_fabric_over_the_edge.html

        Note, fabric's execute is not that nice, because requires a meta-task
    """

    def _dec(fn):
        @functools.wraps(fn)
        def _wrapped(*args, **kwargs):
            for role in roles:
                print(env.roledefs)
                if env.host_string in env.roledefs.get(role, ()):
                    return fn(*args, **kwargs)

        return _wrapped

    return _dec


def _set_args(cmd):
    args = {'cmd': cmd,
            'project_name': env['project_name'],
            'envname': env['envname']}
    return args


def set_engine_branch(engine_branch):
    if engine_branch:
        env['engine_branch'] = engine_branch


def virtualenv_activate():
    do('source {}/bin/activate'.format(env['virtualenv_path']))


def host_type():
    run('uname -a')


def ping():
    return host_type()


def shell(cmd):
    run(cmd)


@with_settings(warn_only=True)
def virtualenv_patch():
    """Various patches e.g. libs from system packages that we need in virtualenv,
       but cannot be installed via pip"""
    # TODO make it more intelligent - e.g. execute patch per supported operating system, then could use warn_only=False
    for cmd in env.get('virtualenv_patch', []):
        do(cmd % env)


def virtualenv_install():
    if 'virtualenv_args' not in env:
        env.virtualenv_args = ''
    virtualenv_binary = run('which virtualenv')
    cmd = '{virtualenv_binary} {virtualenv_args} {virtualenv_path}'.format(virtualenv_binary=virtualenv_binary, **env)
    run(cmd)

    # TODO: remove duplication

    # install defined pip version or latest pip version
    if env.get('pip_version'):
        print(red('pip version defined, installing'))
        run('{virtualenv_path}/bin/pip install pip=={pip_version}'.format(**env))
    else:
        print(yellow('Pip version (env.pip_version) NOT defined, installing the latest one'))
        run('{virtualenv_path}/bin/pip install pip --upgrade'.format(**env))
        # install the latest setuptools version in order
        # to avoid random failures like NameError: name 'sys_platform' is not defined
        print(yellow('Installing also latest setuptools, to avoid strange errors. If that fails, try manually...'))
        run('{virtualenv_path}/bin/pip install setuptools --upgrade'.format(**env))

    virtualenv_install_requirements()


def virtualenv_install_engine():
    engine_repo = getattr(env, 'git_engine_repo', False)
    if engine_repo:
        engine_branch = getattr(env, 'engine_branch', '')
        engine_install_url_components = [engine_repo, engine_branch]
        engine_install_url = '@'.join(filter(None, engine_install_url_components))
        env.pip_args = env.get('pip_args', '--process-dependency-links')
        print(yellow('Installing engine: {git_engine_url}'.format(git_engine_url=engine_install_url)))
        run('{virtualenv_path}/bin/pip install {pip_args} {git_engine_url}'.format(
            git_engine_url=engine_install_url, **env)
        )


def virtualenv_install_requirements():
    # TODO: use cache
    # TODO: don't access internet when not necessary
    env.pip_args = env.get('pip_args', '--process-dependency-links')
    run('{virtualenv_path}/bin/pip install -r {path}/{requirements_file} {pip_args}'.format(**env))
    virtualenv_install_engine()


def create_directories():
    do('mkdir -p dbbackup')
    do('mkdir -p logs')
    do('mkdir -p static')
    do('mkdir -p media')


def django_specific_install():
    virtualenv_install()
    virtualenv_patch()
    create_directories()
    migrate()
    deploy_static()
    set_permissions()


@runs_once
@roles('webserver')
def deploy_static():
    try:
        managepy("collectstatic -v0 --noinput {ignored_files}".format(ignored_files=env.excluded_files))
    except SystemExit:
        print(red("Collectstatic with ignored files failed"))
        if getattr(env, 'retry_collectstatic_without_ignore', False):
            print(yellow("Trying to collect all statics"))
            managepy("collectstatic -v0 --noinput")
            print(green("Collectstatic without ignoring some files succeeded"))
    with settings(warn_only=True):
        managepy('collectmedia')


def set_permissions():
    run('chmod 755 logs', warn_only=True)
    server_type = getattr(env, 'appserver', 'gunicorn')
    if server_type != 'apache':
        # apache requires 755 access to sources (.htaccess file)
        run('chmod 700 %s' % env.project_dir)
    run('chmod 600 .pgpass', warn_only=True)
    run('chmod 700 dbbackup', warn_only=True)


def checkout(branch_name='master'):
    print('')
    print(green("    USING {} branch".format(branch_name)))
    print('')
    with cd(env['path']):
        run('git checkout {}'.format(branch_name))
        # reset hard - in case branch was force-updated
        if branch_name.startswith('origin/'):
            # if branch was already given with origin prefix (e.g. by jenkins) - continue
            pass
        else:
            branch_name = 'origin/{}'.format(branch_name)
        run('git reset --hard {}'.format(branch_name))


def pull():
    with cd(env['path']):
        print("About to git pull - this requires ssh keys to be installed")
        run('git pull')


def fetch(branch_name='master'):
    with cd(env['path']):
        print("About to git fetch - this requires ssh keys to be installed")
        run('git fetch --all')


@runs_once
@roles('webserver')
def migrate():
    skip_migration = getattr(env, 'skip_migration', False)
    if skip_migration:
        print('Skipping migration')
        return
    if get_django_version() < (1, 7):
        print(managepy('migrate --noinput --merge'))
    else:
        print(managepy('migrate'))


@runs_once
def dbbackup():
    print(managepy('dbbackup -z'))


def clear():
    with cd(env['path']):
        run('find . -name "*.pyc" -exec rm -rf "{}" \;')


@with_settings(warn_only=True)
def clear_cache():
    print(managepy('clear_cache'))


def remove_logs():
    with cd('logs'):
        run('rm *.log')


def help(self):
    print("To get command list use fab -l")


def python(command, **kwargs):
    do('source %s/bin/activate && python %s' % (env['virtualenv_path'], command), **kwargs)


def managepy(command, **kwargs):
    with cd(env['path']):
        if getattr(env, 'settings', None):
            _default_settings = env.settings
        else:
            # backwards compatibility
            _default_settings = '%s.settings.%s' % (env.project_name, env.envname)

        if env['envname'] == 'local':
            # we are executing on localhost - could use os
            settings_args = os.environ.get("DJANGO_SETTINGS_MODULE", _default_settings)

        else:
            # executing remotely - could using settings from fabric_config
            settings_args = _default_settings

        python('manage.py %s --settings=%s' % (command, settings_args), **kwargs)


def do(*args, **kwargs):
    """
    Default command runner for Fabric which is run() uses SSH connection to execute commands, that's why
    we need to use a wrapper that changes runner to local(), which is proper for localhost Fabric usage.
    We need to pass bash to local too, as it's default shell is /bin/sh
    """
    if env['envname'] == 'local':
        _do = local
        kwargs.update({'shell': '/bin/bash'})
    else:
        _do = run
    return _do(*args, **kwargs)


class Deployment(object):
    """Base deployment class. Environment classes should inherit from it

        Methods work with fabric decorators.

        Other decorators:

        @staticmethod doesn't work
        @classmethod works, but has to be applied as a last decorator, for example:

            @classmethod
            @runs_once
            def task(...):
                pass

        Note that methods starting with '_' will not be exported
    """

    def __init__(self, localhost=None):
        """
        :param localhost: callable representing localhost
        :return:
        """
        self.localhost = localhost

    @runs_once
    @roles('worker')
    def test_task(self, arg1=None, arg2=33):
        """
        test task - for debugging/testing of fabric scripts
        Example usage:

        fab stage test_task:arg1=11,arg2=3
        """
        print(u"arg1: {} arg2: {}".format(arg1, arg2))
        run('ps uax|wc'.format(self=self))

    def _assume_localhost(self):
        if not hasattr(env, 'envname'):
            print(red('WARNING! No env set. Assuming local env!'))
            if not env.host_string:  # fix for host_string check in @roles decorator
                env.host_string = 'localhost'
            self.localhost()

    @roles('worker')
    def celeryd(self, cmd):
        run('sudo supervisorctl {cmd} {project_name}_{envname}_celeryd:*'.format(**_set_args(cmd)))

    @roles('worker')
    def celerybeat(self, cmd):
        run('sudo supervisorctl {cmd} {project_name}_{envname}_celerybeat'.format(**_set_args(cmd)))

    @roles('worker')
    def celery(self, cmd):
        self.celeryd(cmd)

    @roles('webserver')
    def appserver(self, cmd):
        run('sudo supervisorctl {cmd} {project_name}_{envname}'.format(**_set_args(cmd)))

    @roles('worker')
    def asyncworker(self, cmd):
        server_type = getattr(env, 'asyncworker', 'celery')
        if server_type in ['celery', 'celeryd']:
            self.celery(cmd)
        else:
            print(red('Unsupported asyncworker defined in env'))

    #
    # General methods
    #
    def install(self, branch=None, only_env=False):
        """
        @param branch: git branch
        @param only_env: if True only virtualnv with requirements will be prepared, no migrations
        """
        branch_name = branch or getattr(env, 'git_branch', 'master')
        if exists(env.path):
            with cd(env.path):
                run('git fetch --all --depth 1')
        else:
            cmd = 'git clone {}:{} {}'.format(env.git_server, env.git_repo, env.path)
            run(cmd)
        checkout(branch_name=branch_name)
        pull()
        # TODO: better decision about front
        if 'front' not in env.envname:
            if only_env:
                virtualenv_install()
                virtualenv_patch()
            else:
                django_specific_install()
        # TODO: uncomment if does not work: with settings(warn_only=True):
        self.appserver(cmd='start')
        print(yellow("You might want to run `fab <<env>> deploy` now"))

    def lightdeploy(self, branch=None, engine_branch=None, collectstatic=False):
        print(yellow("LIGHT DEPLOY"))
        branch = branch or getattr(env, 'git_branch', 'master')
        set_engine_branch(engine_branch)
        run('pwd')
        set_permissions()
        with warn_only():
            run("echo $SSH_AUTH_SOCK")
            run("ssh -T git@github.com")
            run("ssh-add -L")
        fetch(branch_name=branch)
        checkout(branch_name=branch)
        pull()  # in certain circumstances reset --hard doesn't update, thus forcing pull BUT after checkout
        virtualenv_install_requirements()
        # nodeenv_install_requirements()
        if getattr(env, 'skip_dbbackup', False):
            print(red('Skipping dbbackup because skip_dbbackup is set in your env or was passed to cmdline'))
        else:
            dbbackup()
        if collectstatic:
            deploy_static()
        clear()
        self.asyncworker('restart')
        with warn_only():
            self.appserver(cmd='stop')
        migrate()
        self.appserver(cmd='start')
        self.celerybeat('restart')
        clear_cache()

    def deploy(self, branch=None, engine_branch=None):
        """
        Deploys latest features from a given branch.

        :param branch: branch name to deploy, default taken from env.git_branch
        :param engine_branch: engine branch name to deploy. Install specific branch of env.git_engine_repo.

        Usage:

        fab devel deploy:new_branch
        fab devel deploy:engine_branch=my_engine_branch
        fab devel deploy:branch=my_branch,engine_branch=my_engine_branch
        """
        import time
        _start = time.time()
        set_engine_branch(engine_branch)
        branch = branch or getattr(env, 'git_branch', 'master')
        self.lightdeploy(branch, collectstatic=True)
        print(green("This deployment took %s seconds" % (time.time() - _start)))


class WithExtraDeployment(Deployment):
    """
    Deployment variant that adds extra server for services like beat
    """
    @roles('extra')
    def celerybeat(self, cmd):
        run('sudo supervisorctl {cmd} {project_name}_{envname}_celerybeat'.format(**_set_args(cmd)))

    @roles('worker')
    def celery(self, cmd):
        self.celeryd(cmd)
