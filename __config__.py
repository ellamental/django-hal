# -*- coding: utf-8 -*-
"""
Configuration for a Python package.

TODO(nick): Make template building easier!
  Maybe make the workflow similar to ./configure && make && make install...

  $ unb template configure --project-name my-project --app-name my_project
  # generates the config file, which the user may or may not edit.
  $ unb template create
  # done inside a directory that has already been `unb template configure`'d

  ... and that's it.

  `unb template create` should be able to read the type of template to create
  from the config file.  It should also remove the config file from the
  directory as the last step in the create process.


Steps to create a new Python package project:

    unb template new pypackage myproject
    cd myproject

    # Edit the config file copied to myproject/__config__.py

    # Build the template.
    unb template build

    # [Optional] Create a project file at ~/.unb-cli.d/projects (see
    # documentation on unb-cli projects for more information on project
    # settings).
    touch ~/.unb-cli.d/projects/myproject

"""

__template__ = 'pypackage'


from collections import OrderedDict
from datetime import datetime
import os
import subprocess


# General Project Information
# ===========================

# Names
# -----

package_name = 'django-hal'  # ex: 'my-project'
# Name of the app as registered at a package repository (e.g., PyPI, NPM, etc).
# e.g., `pip install {{pypi_name}}`

app_name = 'django_hal'  # ex: 'my_project'
# Name used to import the app.
# e.g., `import {{app_name}}`

app_location = app_name
# Location of the app in the project directory.  This is usually the app
# directory, but could be a filename if the app is not in a directory.
# e.g., `cd myproject/{{app_location}}`

project_slug = package_name
# Name of the project as used in urls.
# e.g., http://www.bitbucket.org/organization/{{project_slug}}/issues

verbose_name = 'Django HAL'
# Properly capitalized English name of the project.
# e.g., I worked on {{verbose_name}} all night!


# Descriptions
# ------------

project_headline = "HAL REST utilities for Django"
# A one-line (<= 79 character) description of the project.

project_description = """A set of utilities for building HAL REST APIs in Django."""
# A brief description of the project.  This may be multiple lines.
# Detailed description should go in the README.rst file.

# Other Stuff
# -----------

version = '0.0.1'
# The current (or first) version of the project.


# Organization Information
# ------------------------

organization_name = 'UNB Services'
# Verbose English name of the organization.

organization_url = 'https://www.unb.services'
# URL to the primary home page of the organization.  This may be a
# page aimed at the organization's software projects, but should not be
# specific to this project (unless that's the only option).

organization_slug = 'unbservices'
# Name of the organization as used in urls.


# Author Information
# ------------------

def author_string(name, email):
  return "%s <%s>" % (name, email)


authors_list = [
  ('Nick Zarczynski', 'nick@unb.services'),
]
# Primary author(s) of this package.

authors = ', '.join([author_string(*author) for author in authors_list])
author_names = ', '.join([author[0] for author in authors_list])
author_emails = ', '.join([author[1] for author in authors_list])

# DEPRECATED
author = authors_list[0][0]
author_email = authors_list[0][1]
# TODO(nick): I have to figure out a way to handle the case where only a single
#   name/email is expected.
# DEPRECATED


# Links
# =====

# VCS Information
# ---------------
#
# Information about the version control system.

# repo_host = 'bitbucket.org'
repo_host = 'github.com'

repo_ssh = ''.join(['git@', repo_host, ':',
                    organization_slug, '/', project_slug, '.git'])

repo_url = '/'.join(['https:/',
                     repo_host,
                     organization_slug,
                     project_slug])


# Main
# ----

# The main url:  A general url that could apply to any audience.
project_url = '/'.join(['https:/',
                        repo_host,
                        organization_slug,
                        project_slug])

# Documentation
# -------------

documentation_url = None
# URL for hosted documentation.


# Issue Tracking
# --------------

issue_tracker_url = '/'.join(['https:/',
                              repo_host,
                              organization_slug,
                              project_slug,
                              'issues/'])

issue_contact_email = author_email
# Email that should be used to report issues.
# If `None`, sections that use this will not be written into the README.


# Security
# --------
#
# Note that it's a very good idea to have this prominently displayed (such as
# in the footer of your site).  You want to make it easy for people to report
# and get acknowledgement of that report, so they don't post it on Twitter!
#
# Lookup "security vulnerability report" to get an idea of how most companies
# handle this.

security_reporting_email = author_email
# Email to be used to report security vulnerabilities.

security_reporting_url = None
# URL to direct people that contains information on how to report security
# vulnerabilities found in this software.

# TODO(nick): Add PGP public keys here.
# TODO(nick): Also add a section somewhere for generating checksums of the
#   project (and some utilities for generating and writing them).


# Mailing Lists
# -------------

# Users
# ~~~~~
#
# The "users" mailing list is for discussions of how to use the project.

users_mailing_list = ''
users_mailing_list_subscription_url = None

# Contributers
# ~~~~~~~~~~~~
#
# The "contributers" mailing list is for discussions about the development of
# the project.

contributers_mailing_list = ''
contributers_mailing_list_subscription_url = None


# Chat
# ----
#
# If your project uses chat (IRC, Slack, Gitter, etc.)
#
# These will be injected into the readme, in the order defined.
#
# TODO(nick): Inject these into the README somehow.
# TODO(nick): How to handle IRC?

# chat_services = OrderedDict(
#   # `service-type` = 'irc' or 'slack' or 'gitter' or '...?'
#   gitter={
#     'url': 'https://gitter.im/' + organization_slug + '/' + project_slug,
#   },
#   # slack={
#   #   'url': ''.join(['https://', organization_slug,
#   #                   '.slack.com/messages/', project_slug]),
#   # },
# }


# Copyright and License Information
# =================================

def _copyright_years(start, end):
  start = str(start)
  end = str(end)
  if start == end:
    return end
  else:
    return start + '-' + end

license = 'MIT'

copyright_start_year = datetime.today().year
copyright_end_year = datetime.today().year
copyright_holders_list = [
  author,
]
copyright_years = _copyright_years(copyright_start_year, copyright_end_year)
copyright_holders = ', '.join(copyright_holders_list)
copyright_line = copyright_years + ' ' + copyright_holders
full_copyright_line = 'Copyright (c) ' + copyright_line



# Virtual Environment
# ===================

# If your virtual environment directory is stored in the project itself, this
# will add it to the .gitignore.  Setting it to `None` will not write anything
# to the .gitignore.
venv_dir = None


# Classifiers commonly used in UNB projects
# For a full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
classifiers = [

  # 'Development Status :: 1 - Planning',
  'Development Status :: 2 - Pre-Alpha',
  # 'Development Status :: 3 - Alpha',
  # 'Development Status :: 4 - Beta',
  # 'Development Status :: 5 - Production/Stable',
  # 'Development Status :: 6 - Mature',
  # 'Development Status :: 7 - Inactive',

  # 'Environment :: Console',
  # 'Environment :: MacOS X',
  'Environment :: Web Environment',
  # 'Environment :: Web Environment :: Mozilla',
  # 'Environment :: X11 Applications',
  # 'Environment :: X11 Applications :: Gnome',
  # 'Environment :: X11 Applications :: GTK',
  # 'Environment :: X11 Applications :: KDE',
  # 'Environment :: X11 Applications :: Qt',

  'Framework :: Django',
  'Framework :: Django :: 1.8',
  # 'Framework :: Flask',
  # 'Framework :: IPython',
  # 'Framework :: Sphinx',

  # 'Intended Audience :: Developers',
  # 'Intended Audience :: End Users/Desktop',

  'License :: OSI Approved :: MIT License',
  # 'License :: Other/Proprietary License',

  'Natural Language :: English',

  # 'Operating System :: Android',
  # 'Operating System :: iOS',
  # 'Operating System :: MacOS :: MacOS X',
  'Operating System :: OS Independent',
  # 'Operating System :: POSIX :: Linux',

  'Programming Language :: Python',
  'Programming Language :: Python :: 2.7',
  # 'Programming Language :: Python :: 2 :: Only',
  # 'Programming Language :: Python :: 3',
  # 'Programming Language :: JavaScript',
  # 'Programming Language :: Unix Shell',

  # 'Topic :: Documentation :: Sphinx',
  # 'Topic :: Internet',
  # 'Topic :: Internet :: WWW/HTTP :: WSGI',
  # 'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
  # 'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
  # 'Topic :: Internet :: WWW/HTTP :: WSGI :: Server',
  # 'Topic :: Software Development :: Build Tools',
  # 'Topic :: Software Development :: Code Generators',
  # 'Topic :: Software Development :: Documentation',
  # 'Topic :: Software Development :: Libraries',
  # 'Topic :: Software Development :: Libraries :: Application Frameworks',
  # 'Topic :: Software Development :: Libraries :: Python Modules',
  # 'Topic :: Software Development :: Testing',
  # 'Topic :: Software Development :: User Interfaces',
  # 'Topic :: Software Development :: Version Control',
  # 'Topic :: System :: Installation/Setup',
  # 'Topic :: Text Editors :: Emacs',
  # 'Topic :: Text Processing :: Markup',
  # 'Topic :: Utilities',
]


# Before and After Scripts
# ========================

def before(config):
  print 'Building project for %s' % verbose_name


def after(config):
  if not os.path.exists('.git'):
    subprocess.call(['git', 'init'])
    subprocess.call(['git', 'remote', 'add', 'origin', repo_ssh])
    print "Git repo created, origin added."

  print """
========================================================================
Completed build of python project template for: {verbose_name}
========================================================================

Next steps:

mkvirtualenv {package_name}
unb pip install
unb docs build


""".format(package_name=config.get('package_name', ''),
           verbose_name=config.get('verbose_name', ''))
