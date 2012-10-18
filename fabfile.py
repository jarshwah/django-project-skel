from fabric.api import *
from fabric.contrib.files import exists, upload_template
# Default release is 'current'
env.release = 'current'

def production():
    """Production server settings"""
    env.settings = 'production'
    env.user = 'django'
    env.path = '/home/%(user)s/sites/{{ project_name }}' % env
    env.hosts = ['host.sub.domain.com']

def setup():
    """
    Setup a fresh virtualenv and install everything we need so it's ready to deploy to
    """
    push_repo()
    run('mkdir -p %(path)s; cd %(path)s; virtualenv --no-site-packages .; mkdir releases; mkdir media; mkdir static' % env)
    upload_template('{{ project_name }}/__local_settings.py', '%(path)s/local_settings.py' % env, context=None, use_sudo=False, backup=False, mode=0770)
    clone_repo()
    checkout_latest()
    install_requirements()
    symlink_current_release()
    deploy_init_scripts()
    #setup_celery()
    start_servers()

def deploy():
    """Deploy the latest version of the site to the server and restart nginx"""
    push_repo()
    checkout_latest()
    install_requirements()
    symlink_current_release()
    deploy_config_files()
    migrate()
    restart_server()

def push_repo():
    """Push local repo to server"""
    # bit of a hack, must have a remote setup called 'django1' which points to the right server.. FIXME
    local('git push django1 master')

def clone_repo():
    """Do initial clone of the git repo"""
    run('cd %(path)s; git clone /home/%(user)s/git/repositories/{{ project_name }}.git repository' % env)

def checkout_latest():
    """Pull the latest code into the git repo and copy to a timestamped release directory"""
    import time
    env.release = time.strftime('%Y%m%d%H%M%S')
    run("cd %(path)s/repository; git pull origin master" % env)
    run('cp -R %(path)s/repository %(path)s/releases/%(release)s; rm -rf %(path)s/releases/%(release)s/.git*' % env)

def install_requirements():
    """Install the required packages using pip"""
    run('cd %(path)s; %(path)s/bin/pip install -r ./releases/%(release)s/requirements.txt' % env)

def setup_celery():
    sudo('mkdir -p /var/log/celery; mkdir -p /var/run/celery')
    sudo('chown -R django:django /var/log/celery; chown -R django:django /var/run/celery;')

def symlink_current_release():
    """Symlink our current release, uploads and settings file"""
    with settings(warn_only=True):
        run('cd %(path)s; rm releases/previous; mv releases/current releases/previous;' % env)
        run('cd %(path)s; ln -s %(release)s releases/current' % env)
        """ production settings"""
        run('cd %(path)s; cp local_settings.py releases/current/{{ project_name }}/local_settings.py' % env)
    with settings(warn_only=True):
        run('cd %(path)s/releases/current; ../../bin/python manage.py collectstatic --noinput' % env)
    with settings(warn_only=True):
        run('cd %(path)s/releases/; ls -t1 | tail -n +6 | xargs rm -r' % env) # remove all entries older than 3 releases (current/previous) + 1

def deploy_init_scripts():
    upload_template('config/uwsgi.init',    '/etc/init.d/uwsgi',    context=None, use_sudo=True, backup=False, mode=0755)
    sudo('chkconfig uwsgi on')
    #upload_template('config/celeryd',       '/etc/init.d/celeryd',  context=None, use_sudo=True, backup=False, mode=0755)
    #sudo('chkconfig celeryd on')

def deploy_config_files():
    """Helper for deploying relevant Config Files"""
    upload_template('config/uwsgi-emperor.ini',         '/etc/uwsgi/{{ project_name }}.ini',          context=None, use_sudo=False, backup=False, mode=0644)
    upload_template('config/{{ project_name }}.conf',   '/etc/nginx/conf.d/{{ project_name }}.conf',  context=env, use_sudo=True, backup=False, mode=0644)
    #upload_template('config/celeryd.conf',              '/etc/default/celeryd',                       context=None, use_sudo=True, backup=False, mode=0644)

def migrate():
    """Run our migrations"""
    run('cd %(path)s/releases/current; ../../bin/python manage.py syncdb --noinput' % env)

def rollback():
    """
    Limited rollback capability. Simply loads the previously current
    version of the code. Rolling back again will swap between the two.
    """
    run('cd %(path)s; mv releases/current releases/_previous;' % env)
    run('cd %(path)s; mv releases/previous releases/current;' % env)
    run('cd %(path)s; mv releases/_previous releases/previous;' %env)
    restart_server()

def start_servers():
    """ Initially starts the web server and app server """
    sudo('/sbin/service uwsgi start')
    sudo('/sbin/service nginx start')

def restart_server():
    """Restart the web server"""
    with settings(warn_only=True):
        reload_uwsgi()
        reload_nginx()
        #reload_celery()

def reload_uwsgi():
    """Reloads the uwsgi server"""
    sudo('/sbin/service uwsgi reload')

def reload_nginx():
    """Restarts nginx"""
    sudo('/sbin/service nginx reload')

def reload_celery():
    """Restarts Celery"""
    sudo('/sbin/service celeryd restart')
