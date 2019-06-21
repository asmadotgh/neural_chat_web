from fabric.api import run, cd, sudo, get, put, env, local, prefix
from fabric.contrib.files import exists
from contextlib import contextmanager

from project import settings

import os

env.use_ssh_config = True

FILE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

MYSQL_ROOT_PASSWORD = "[[ EDITME MySQL root user password ]]"

SETUP_DIRECTORY = "/opt/"
CODE_HOME = os.path.join(SETUP_DIRECTORY, "django")

DIRECTORIES_TO_CREATE = ()

GITHUB_SSH_URL = "[[ EDITME URL to your github fork of this project ]]"

VIRTUAL_ENVIRONMENT = "/opt/virtualenvironment/"

class FabricException(Exception):
    pass


@contextmanager
def virtualenv():
    with prefix('source {0}bin/activate'.format(VIRTUAL_ENVIRONMENT)):
        yield

def test():
    run("ls")


def deploy():
    with cd(CODE_HOME):
        run("git reset --hard")
        run("git clean -f -d")
        run("git pull origin master")

        with virtualenv():
            sudo('pip install -r requirements.txt')

            # run('cp /opt/passwords.py src')

            sudo("python3 manage.py migrate", user="www-data")

            sudo("python3 manage.py collectstatic --noinput", user="www-data")


    sudo('service uwsgi restart')


def shell():
    with cd(CODE_HOME):
        sudo("python manage.py shell", user="www-data")


def setup_db():
    with cd(SETUP_DIRECTORY):
        sudo('service mysql stop')
        sudo('nohup /usr/sbin/mysqld --skip-grant-tables --skip-networking > /dev/null 2>&1 &')
        sudo("mysql -uroot -e 'use mysql; update user set authentication_string=PASSWORD(\"{0}\") where User=\"root\"; flush privileges;'".format(MYSQL_ROOT_PASSWORD))
        sudo("mysqladmin -u root -p{0} shutdown".format(MYSQL_ROOT_PASSWORD))
        sudo('sudo service mysql start')

        for command in _get_configure_db_commands(MYSQL_ROOT_PASSWORD):
            sudo(command)


def deploy_crontab():
    put(os.path.join(FILE_DIRECTORY, '../crontab'), '/tmp/crontab')
    sudo('crontab < /tmp/crontab')


def setup_server():
    sudo('apt-get update')

    # get the programs we'll need
    sudo('apt-get -y install python3.6 python-setuptools git nginx mysql-server python3-mysqldb')
    sudo('apt-get -y install python3-pip python3-dev build-essential default-libmysqlclient-dev uwsgi-plugin-python3')
    sudo('apt-get -y install libffi-dev libssl-dev libxml2-dev libxslt1-dev')
    sudo('apt-get -y install yui-compressor')

    sudo('apt-get -y remove uwsgi')  # not sure why it's even there on some servers

    with virtualenv():
        run('pip3 install uwsgi')

    sudo('apt-get -y install uwsgi-plugin-python3')

    # get code
    sudo('mkdir -p ' + SETUP_DIRECTORY)
    sudo('chown {0}:www-data '.format(env.user) + SETUP_DIRECTORY)
    for d in DIRECTORIES_TO_CREATE:
        sudo('mkdir -p ' + d)
        sudo('chown {0}:www-data '.format(env.user) + d)
        sudo('chmod g+w ' + d)

    with cd(SETUP_DIRECTORY):

        run('git config --global user.name "Deploy"')
        sudo('mkdir -p /home/{0}/.ssh/'.format(env.user))
        _put_key_file('github')

        setup_db()

        run("touch ~/.ssh/config")
        run(
            'if ! cat ~/.ssh/config | grep "github"; then echo -e "Host github.mit.edu\n    User git\n    IdentityFile ~/.ssh/github" >> ~/.ssh/config; fi;')

        if exists('/opt/code'):
            run('rm -rf /opt/code')
        if not exists("/opt/code"):
            run('git init code')
            with cd('/opt/code'):
                run('git remote add -f origin {0}'.format(GITHUB_SSH_URL))
                run('git pull origin master')
        if exists(CODE_HOME):
            run('rm ' + CODE_HOME)
        run('ln -s {0} {1}'.format("/opt/code/", CODE_HOME))

        put('{0}/nginx-default-conf'.format(os.path.dirname(FILE_DIRECTORY)), '/etc/nginx/sites-enabled/default',
            use_sudo=True)
        put('{0}/nginx-conf'.format(os.path.dirname(FILE_DIRECTORY)), '/etc/nginx/nginx.conf', use_sudo=True)
        put('{0}/uwsgi-systemd'.format(os.path.dirname(FILE_DIRECTORY)), '/etc/systemd/system/uwsgi.service',
            use_sudo=True)

        sudo('[ -d `command -v systemctl` ] || systemctl daemon-reload')  # run systemctl only if it exists
        sudo('systemctl enable uwsgi')

    sudo('apt-get install -y certbot python-certbot-nginx -t stretch-backports')
    sudo('certbot --nginx')


    sudo('mkdir -p /opt/staticfiles')
    sudo('chown www-data:www-data /opt/staticfiles')
    sudo('mkdir -p /opt/media')
    sudo('chown www-data:www-data /opt/media')

    sudo('mkdir -p /var/log/django/')
    sudo('chown www-data:www-data /var/log/django/')
    sudo('touch /var/log/django/django.log')
    sudo('chown www-data:www-data /var/log/django/django.log')
    sudo('chmod g+w /var/log/django/')
    sudo('touch /var/log/uwsgi.log')
    sudo('chmod 777 /var/log/uwsgi.log')
    sudo('service nginx restart')

    deploy_crontab()

    deploy()


def create_superuser():
    with cd(CODE_HOME):
        with virtualenv():
            sudo("python manage.py createsuperuser", user="www-data")


def tail_log():
    with cd(CODE_HOME):
        sudo("tail -n100 /var/log/django/django.log", user="www-data")


def copy_db():
    run("mysqldump {1} -uroot -p{0} > ".format(MYSQL_ROOT_PASSWORD,
                                               settings.DATABASES['default']['NAME']) + "/tmp/dump.sql")
    get("/tmp/dump.sql", "/tmp/dump.sql")
    local("mysql {0} -uroot < /tmp/dump.sql".format(settings.DATABASES['default']['NAME']))


def _put_key_file(localkeyname):
    localpath = os.path.join(FILE_DIRECTORY, 'keys', localkeyname)
    put(localpath, '/home/{0}/.ssh/'.format(env.user))
    sudo('chmod 600 /home/{0}/.ssh/{1}'.format(env.user, localkeyname))


def _get_configure_db_commands(root_password):
    # configure our db
    username = settings.DATABASES['default']['USER']
    db = settings.DATABASES['default']['NAME']
    password = settings.DATABASES['default']['PASSWORD']

    if root_password:
        root_password = "-p" + root_password

    commands = (
        "mysql -uroot {0} -e 'CREATE DATABASE IF NOT EXISTS {1}'".format(root_password, db),
        "mysql -uroot {0} -e 'CREATE USER IF NOT EXISTS \"{1}\"@\"localhost\" IDENTIFIED BY \"{2}\"'".format(root_password, username, password),
        "mysql -uroot {0} -e 'GRANT ALL PRIVILEGES ON {2}.* TO {3}@localhost'".format(
            root_password, password, db, username),
        "mysql -uroot {0} -e 'ALTER DATABASE {1} CHARACTER SET \"utf8\" COLLATE \"utf8_unicode_ci\"'".format(
            root_password, db),

        "mysql -uroot {0} -e 'FLUSH PRIVILEGES'".format(root_password),
    )
    return commands


def configure_local_db(root_password=""):
    for command in _get_configure_db_commands(root_password):
        local(command)

    print("MySQL configured successfully!")


def create_ssh_key(keypath="github"):
    keyfiles_dir = "{0}/keys/".format(FILE_DIRECTORY)
    local("mkdir -p {0}".format(keyfiles_dir))
    keypath = os.path.join(keyfiles_dir, keypath)
    if not os.path.isfile(keypath):
        local("ssh-keygen -b 2048 -t rsa -f {0} -q -N \"\"".format(keypath))

        print("Created SSH Key at: " + keypath)

    return keypath + ".pub"
