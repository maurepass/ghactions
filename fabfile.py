# # encoding: utf-8
# # flake8: noqa
from __future__ import with_statement

from deploy.base_fabfile import *
from deploy.utils import extend_module_with_instance_methods

from fabric_config import CONFIG_MAP


def stage():
    config = CONFIG_MAP["stage"]()
    env.update(config.env)


def prod():
    config = CONFIG_MAP["prod"]()
    env.update(config.env)


instance = Deployment()  # type: ignore

extend_module_with_instance_methods(__name__, instance)

#
#
#
#
# import json
# import os
# import re
# from collections import ChainMap
#
# from fabric.api import cd, env, local, put, run
# from fabric.colors import green, magenta, red, yellow
# from fabric.contrib import files
#
#
#
# import deploy_dms
#
#
# def _check_secret_and_warn(key, help_text, default="", override=False):
#     """
#     Checks that the secret exists and adds it if it does not yet.
#
#     If the override option is given and a truthy value in default, it will be used to override the existing secret.
#
#     If the value is still empty after all that, the help_text will be printed to instruct the user on how he should
#     set this secret.
#     """
#     v = env.app.secrets
#     key = key.split(".")
#     for idx, p in enumerate(key):
#         if p in v:
#             if idx == len(key) - 1 and default and override:
#                 v[p] = default
#             v = v[p]
#         else:
#             if idx < len(key) - 1:
#                 v[p] = {}
#             else:
#                 v[p] = default
#             v = v[p]
#     if v == "":
#         print(
#             red(
#                 'Secret needs to be set on server: "%(key)s"'
#                 % dict(key=".".join(key), secrets_file=env.app.secrets_file)
#             )
#         )
#         print(yellow("  --> " + help_text))
#     return v
#
#
# def prepare_secrets():
#     with deploy_dms.patch_remote_file(env.app.secrets_file, mode=0o600) as secrets_file:
#         secrets = json.loads(secrets_file.content or "{}")
#         env.app.secrets = secrets
#         # check that we have all secrets setup:
#         _check_secret_and_warn(
#             "secret-key",
#             "Set to the secret key used by django",
#             default=deploy_dms.generate_password(60),
#         )
#         _check_secret_and_warn(
#             "time-zone",
#             "Set to the desired timezone of the admin interface.",
#             default="Europe/Zurich",
#         )
#         _check_secret_and_warn(
#             "background-task.time-limit",
#             "Set the time limit for background tasks.",
#             default="300",
#         )
#         _check_secret_and_warn(
#             "storage.time-series-quota",
#             "Set the TimeSeries storage quota in GB.",
#             default="10",
#         )
#         _check_secret_and_warn(
#             "event-logger-max-retention-days",
#             "Set to the maximum retention time of events in the " "event logger.",
#             default="-1",
#         )
#         _check_secret_and_warn(
#             "recaptcha-secrets.create_profile",
#             "Set to the reCAPTCHA secret for the visible captcha "
#             "displayed when creating profiles. "
#             "Leaving this empty will disable reCAPTCHA.",
#         )
#         _check_secret_and_warn(
#             "recaptcha-secrets.login",
#             "Set to the reCAPTCHA secret for the invisible captcha "
#             "at the login view. "
#             "Leaving this empty will disable reCAPTCHA.",
#         )
#         _check_secret_and_warn(
#             "recaptcha-site-keys.create_profile",
#             "Set to the reCAPTCHA site key for the visible "
#             "captcha displayed when creating profiles. "
#             "Leaving this empty will disable reCAPTCHA.",
#         )
#         _check_secret_and_warn(
#             "recaptcha-site-keys.login",
#             "Set to the reCAPTCHA site key for the invisible captcha "
#             "at the login view. "
#             "Leaving this empty will disable reCAPTCHA.",
#         )
#
#         env.app.sentry["backend"]["dsn"] = _check_secret_and_warn(
#             "sentry.backend.dsn",
#             "Set the sentry DSN for the backend. "
#             "Blank to disable sentry in backend.",
#         )
#         env.app.sentry["frontend"]["dsn"] = _check_secret_and_warn(
#             "sentry.frontend.dsn",
#             "Set to sentry DSN for the frontend. "
#             "Blank to disable sentry in frontend.",
#         )
#
#         _check_secret_and_warn(
#             "secret-key",
#             "Set to a unpredictable random string. It will be used to sign various things "
#             "in django.",
#         )
#         _check_secret_and_warn(
#             "email-host", "Set to the email server host.", default="mail.infomaniak.ch"
#         )
#         _check_secret_and_warn(
#             "email-port", "Set to the email server SMTP port.", default="25"
#         )
#         _check_secret_and_warn("email-user", "Set to the email server username.")
#         _check_secret_and_warn(
#             "email-password",
#             "Set to the email server password. Empty for no authentication.",
#         )
#         _check_secret_and_warn(
#             "vpn-2fa-allowed-ips", "Set to the VPN IP range.", default="10.0.0.0/8"
#         )
#         env.app.postgres["password"] = _check_secret_and_warn(
#             "postgres.password",
#             'Set to the postgres password of the "%(postgres.user)s" user.' % env.app,
#             default=env.app.postgres["password"],
#             override=True,
#         )
#         env.app.supervisor["password"] = _check_secret_and_warn(
#             "supervisor.password",
#             "Set the password for the supervisorctl access",
#             default=deploy_dms.generate_password(),
#         )
#
#         # store:
#         secrets_file.content = json.dumps(
#             env.app.secrets, sort_keys=True, indent=2, separators=(",", ": ")
#         )
#
#
# def prepare_brelag_secrets():
#     with deploy_dms.patch_remote_file(env.app.secrets_file, mode=0o600) as secrets_file:
#         env.app.brelag["saferpay_customer_id"] = _check_secret_and_warn(
#             "brelag.saferpay_customer_id",
#             "brelag.saferpay_customer_id",
#         )
#         env.app.brelag["saferpay_terminal_id"] = _check_secret_and_warn(
#             "brelag.saferpay_terminal_id",
#             "brelag.saferpay_terminal_id",
#         )
#         env.app.brelag["saferpay_api_url"] = _check_secret_and_warn(
#             "brelag.saferpay_api_url",
#             "brelag.saferpay_api_url",
#         )
#         env.app.brelag["saferpay_api_username"] = _check_secret_and_warn(
#             "brelag.saferpay_api_username",
#             "brelag.saferpay_api_username",
#         )
#         env.app.brelag["saferpay_api_password"] = _check_secret_and_warn(
#             "brelag.saferpay_api_password",
#             "brelag.saferpay_api_password",
#         )
#         env.app.brelag["fusion_one_equipment_id"] = _check_secret_and_warn(
#             "brelag.fusion_one_equipment_id",
#             "brelag.fusion_one_equipment_id",
#         )
#         env.app.brelag["manual_payment_notify_email"] = _check_secret_and_warn(
#             "brelag.manual_payment_notify_email",
#             "brelag.manual_payment_notify_email",
#         )
#
#         # store:
#         secrets_file.content = json.dumps(
#             env.app.secrets, sort_keys=True, indent=2, separators=(",", ": ")
#         )
#
#
# def multi(mapping, app_environment):
#     """
#     Selects the hosts. Must be called before ``environment`` task.
#
#     :param mapping: The host mapping. See README.
#     :param app_environment: The app environment to deploy.
#     """
#     deploy_dms.setup_multi_deployment(mapping=mapping, app_environment=app_environment)
#
#
# def environment(dms_files_root="/var/www/dms"):
#     """
#     Prepares the environment. Must be called before ``deploy`` task.
#
#     :param dms_files_root: The web file root to use.
#     """
#
#     deploy_dms.configure_base_env(dms_files_root=dms_files_root)
#     deploy_dms.configure_brelag_env()
#
#
# def deploy():
#     """
#     Deploys or updates a DMS instance. ``environment`` task must be called before this task.
#
#     This runs in two privilege levels: The deploy_user only has access to the current environment.
#     When system user credential are provided, the script elevates to that user and is able to install / update
#     the system as well.
#     """
#
#     print(magenta('Deploying to "%(environment)s" environment ...' % env.app))
#
#     # Setup base system
#     deploy_dms.maybe_setup_base_system_with_system_user()
#
#     with deploy_dms.deploy_user():
#         #
#         # PREPARE FOR THE NEW ENVIRONMENT
#         #
#
#         # Setup:
#         deploy_dms.setup_virtualenv()
#
#         # Prepare secrets:
#         prepare_secrets()
#         if env.app.option_brelag:
#             prepare_brelag_secrets()
#
#         # Select what needs to be deployed:
#         core_deploy = [
#             "api",
#             "client",
#             "core",
#             "event_log",
#             "commerce",
#             "brelag",
#             "manage.py",
#             "dms/__init__.py",
#             "dms/celery.py",
#             "dms/settings.py",
#             "dms/urls.py",
#             "dms/wsgi.py",
#             "requirements.txt",
#             "requirements_prod.txt",
#         ]
#
#         to_deploy = set()
#         to_deploy.update(core_deploy)
#
#         # Prepare app directory:
#         run("mkdir -p %(app_dir)s" % env.app)
#         # Prepare static and media directories:
#         run("mkdir -p %(dj_static_dir)s" % env.app)
#         run("mkdir -p %(media_dir)s" % env.app)
#         # Prepare directory for celery and logging:
#         run("mkdir -p %(home_dir)s/celery" % env.app)
#         run("mkdir -p %(home_dir)s/log" % env.app)
#         # Prepare supervisor directories
#         run("mkdir -p %(home_dir)s/supervisor/conf.d" % env.app)
#
#         # Check if we need to migrate from the old git based deployment:
#         if files.exists("%(app_dir)s/.git" % env.app):
#             print(red("Will remove the git repository from the server!"))
#
#             remote_deployed_files = (
#                 deploy_dms.deploy_git_archive_get_file_list_filename("server")
#             )
#
#             with deploy_dms.app_dir():
#                 run(
#                     "git archive --format=tar HEAD | tar -tf- > %s"
#                     % remote_deployed_files
#                 )
#                 run("echo .git/ >> %s" % remote_deployed_files)
#
#         #
#         # UPGRADE THE CRITICAL COMPONENTS AS QUICKLY AS POSSIBLE
#         #
#
#         deploy_dms.deploy_git_archive("server", to_deploy)
#
#         with deploy_dms.app_dir(), deploy_dms.enter_virtualenv():
#             # Install python dependencies:
#             print(green("Installing python dependencies ..."))
#             run("which pip")
#             run("pip install --upgrade pip")
#             run("pip install -r requirements.txt")
#             run("pip install --no-binary uwsgi,psycopg2 -r requirements_prod.txt")
#
#             # Put private_settings template:
#             print(green("Installing settings files ..."))
#             files.upload_template(
#                 "dms/secrets.py.template", destination="dms/secrets.py", context=env.app
#             )
#             files.upload_template(
#                 "dms/private_settings.py.template",
#                 destination="dms/private_settings.py",
#                 context=env.app,
#             )
#             if env.app.option_brelag:
#                 files.upload_template(
#                     "dms/brelag_settings.py.template",
#                     destination="dms/brelag_settings.py",
#                     context=env.app,
#                 )
#             # Migrate:
#             print(green("Migrate database ..."))
#             run("python ./manage.py migrate")
#
#             # Put uwsgi.ini template (this will probably reload the server)
#             print(green("Installing uwsgi.ini ..."))
#             run("mkdir -p uwsgi" % env.app)
#             files.upload_template(
#                 "uwsgi/dms.ini.template",
#                 destination="%(uwsgi.ini-name)s" % env.app,
#                 context=env.app,
#             )
#
#             # Put nginx template
#             print(green("Installing nginx config ..."))
#             run("mkdir -p nginx" % env.app)
#             # TODO: Disabling for now
#             # files.upload_template('nginx/dms.conf.template', destination='%(nginx.conf-name)s' % env.app,
#             #                       context=env.app)
#
#             # Put supervisord template
#             print(green("Installing supervisord config ..."))
#             files.upload_template(
#                 "supervisord/supervisord.conf.template",
#                 destination="%(home_dir)s/supervisor/supervisord.conf" % env.app,
#                 context=env.app,
#                 mode=0o600,
#             )
#
#             # Make sure it is reloaded:
#             print(green("Restart uwsgi vassal ..."))
#             run("touch %(uwsgi.ini-name)s" % env.app)
#
#         # Restart supervisord
#         print(green("Restart all supervised programs ..."))
#         if (
#             run(
#                 "supervisorctl -c %(home_dir)s/supervisor/supervisord.conf avail"
#                 % env.app,
#                 warn_only=True,
#                 quiet=True,
#             ).return_code
#             != 0
#         ):
#             # Start supervisord as it is not running yet
#             print(green("Starting supervisord"))
#             run("supervisord -c %(home_dir)s/supervisor/supervisord.conf" % env.app)
#         else:
#             # supervisord is already running, reread config and restart all programs
#             run(
#                 "supervisorctl -c %(home_dir)s/supervisor/supervisord.conf reread"
#                 % env.app
#             )
#             run(
#                 "supervisorctl -c %(home_dir)s/supervisor/supervisord.conf update all"
#                 % env.app
#             )
#             run(
#                 "supervisorctl -c %(home_dir)s/supervisor/supervisord.conf restart all"
#                 % env.app
#             )
#
#         #
#         # RUN EXPENSIVE MIGRATIONS IN THE BACKGROUND WHILE THE NEW SYSTEM IS UP
#         #
#
#         with deploy_dms.app_dir(), deploy_dms.enter_virtualenv():
#             # Collect static files:
#             print(green("Collecting static files ..."))
#             run("python ./manage.py collectstatic --no-input")
#
#             # Reevaluate all rules:
#             # print(green('Reevaluating all permission rules to make sure they are up-to-date ...'))
#             # run('python ./manage.py reevaluate-all-rules')
#
#         # Install crontab to automatically start supervisord at system boot:
#
#         print(green("Ensuring supervisord will be automatically (re)started ..."))
#         files.upload_template(
#             "supervisord/ensure-running.sh.template",
#             destination="%(home_dir)s/supervisor/ensure-running.sh" % env.app,
#             context=env.app,
#             mode=0o755,
#         )
#         deploy_dms.update_cron_job(
#             tag="Supervisor [nFTNUai12]",
#             when="* * * * *",
#             command="%(home_dir)s/supervisor/ensure-running.sh" % env.app,
#         )
#
#         # Grant all permissions to CodeGen file:
#         run("chmod 777 %(app_dir)s/brelag/egate/CodeGen" % env.app)
#
#         deploy_dms.pickup_config_files()
