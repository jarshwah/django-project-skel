{% comment %}

## Using this Project Template ##

```bash
django-admin.py startproject --template https://github.com/jarshwah/django-project-skel/zipball/master --extension py,md,conf,ini,html YOURPROJECTNAME
```

{% endcomment %}

# {{ project_name|title }} Django Project #

## Prerequisites ##

- python >= 3.4

## Installation ##

### Clone the code ###
Obtain the url to your git repository.

```bash
git clone <URL_TO_GIT_RESPOSITORY> {{ project_name }}
```

### Setup Virtual Environment

```bash
cd {{ project_name }}
pyvenv venv
```

### Install requirements ###
```bash
source bin/activate
pip install -r requirements.txt
```

### Configure local project settings ###
```bash
cp {{ project_name }}/__local_settings.py {{ project_name }}/local_settings.py
vim {{ project_name }}/local_settings.py
```

### Migrate Database ###
```bash
python manage.py migrate
```

### Configure Logging ###
```bash
sudo mkdir -p /var/log/django
sudo chmod +w /var/log/django

# or simply disable logfile logging locally in settings.py
```

## Running ##
```bash
python manage.py runserver
```

Open browser to http://127.0.0.1:8000

# Deploying to Production (Redhat 5) Example #

## Note: This example is out of date, but left here as an example of using fabric

Much of the installation setup has come from a 5 part series:

http://www.abidibo.net/blog/2012/04/30/deploy-django-applications-nginx-uwsgi-virtualenv-south-git-and-fabric-part-1/

```bash

# as root on the server

useradd -s /bin/bash -d /home/django django
echo "YOURUSERPASSWORD" | passwd --stdin django
echo "django ALL=(ALL) ALL" >> /etc/sudoers

# enable EPEL (for nginx and others)
rpm -ivh http://mirror.optus.net/epel/5/i386/epel-release-5-4.noarch.rpm

sudo yum -y install python python-devel python-setuptools git libpcre3 libpcre3-dev nginx gcc
chkconfig nginx on
sudo easy_install pip
pip install virtualenv uwsgi
mkdir -p /etc/uwsgi

/sbin/iptables -A INPUT -m state --state NEW -p tcp --dport 8000 -j ACCEPT
mkdir /var/log/django
chown -R django:django /var/log/django
chmod -R 770 /var/log/django

# disable selinux
vim /etc/sysconfig/selinux
# change to disabled - then reboot the server (sigh)

shutdown -r now
```

Now we need to do some preparation work on the production server as our django user

```bash
su - django
cd /home/django
mkdir -p git/repositories
cd git/repositories
mkdir {{ project_name }}.git
cd {{ project_name }}.git
git init --bare
```

At this point, you probably want to add your ssh key to the authorized_keys file of the django user to avoid
constantly typing the ssh password of the django user. Locally:

```bash
# from your machine
ssh-copy-id django@prodserver
```

Add the production git repository as a remote from our local machine

```bash
workon {{ project_name }}
git remote add django1 django@host.sub.domain.com:git/repositories/{{ project_name }}.git
git push django1 master
```

Then we use Fabric to do deployment

```bash
workon {{ project_name }}

vim fabfile.py
# edit in your production host in the hosts attribute within the production() function
# then...

fab production setup

# now go to your server, and modify /home/django/sites/{{ project_name }}/local_settings.py with production settings

fab production deploy
fab production rollback
fab production rollback # continually switches between "current" and "previous" releases

```
