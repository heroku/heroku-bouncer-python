from setuptools import setup

setup(
    name = "heroku-bouncer",
    description = "WSGI middleware that requires Heroku OAuth for all requests.",
    version = "1.3",
    author = "Jacob Kaplan-Moss",
    author_email = "jacob@heroku.com",
    url = "http://github.com/heroku/heroku-bouncer-python",
    py_modules = ['heroku_bouncer'],
    install_requires = ['requests>=1.2', 'wsgi-oauth2>=0.1.3'],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware'
    ]
)
