===================
 Django Cronrunner
===================

A simple Django app for setting up and running cron jobs. Requires python crontab module https://pypi.python.org/pypi/python-crontab

Getting Started
===============

After installing simply create a folder called "cron" in any Django application directory. Within that directory create python files named whatever you want. Each file must contain a function called "import_items" which will be passed a ScheduledImport object. Now you will be able to setup scheduled imports from within the Django admin.
