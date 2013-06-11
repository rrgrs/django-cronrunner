from setuptools import setup

setup(
    name='django-cronrunner',
    version='0.1.0',
    description='A django app for setting up and running cron jobs and data imports.',
    long_description=open('README.md').read(),
    author='Ryan Rogers',
    author_email='ryan.rogers@ckrinteractive.com',
    url='https://github.com/rrgrs/django-cronrunner',
    license='BSD',
    packages=[
        'cronrunner',
        'cronrunner.management',
        'cronrunner.management.commands',
    ],
    keywords = "django cron imports",
    requires=[
        'Django',
        'crontab',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
