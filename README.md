# Heroku Bouncer - Python edition

WSGI middleware that requires Heroku OAuth for all requests.

Inspired and cribbed from [heroku-bouncer](https://github.com/heroku/heroku-bouncer).

## Installation

```
pip install heroku-bouncer
```

## Usage

1. Create your OAuth client using `/auth/heroku/callback/` as your callback
   endpoint:

        heroku clients:create likeaboss https://likeaboss.herokuapp.com/auth/heroku/callback/

2. Set `SECRET_KEY`, `HEROKU_OAUTH_ID` and `HEROKU_OAUTH_SECRET` in your environment:

        heroku config:set SECRET_KEY=...
        heroku config:set HEROKU_OAUTH_ID=...
        heroku config:set HEROKU_OAUTH_SECRET=...

3. Wire up the middleware. See [options](#options) for the options you can
   pass in here:

        import heroku_bouncer
        from your.wsgi.application import app

        app = heroku_bouncer.bouncer(app)

4. This will require Heroku OAuth for all access to the app. The user
   (i.e. email address of the Heroku account) will be stored in `"REMOTE_USER"`
   in the WSGI environ. For more access to the authenticated user, check
   out [the session object](#session) (see below).

<a name="session"/>
## The session object

For more details about the user, you can access `"wsgioauth2.session"` in the
WSGI environ. You'll probably be getting this environ from whatever framework
you're using. For example, in Django you'll find this in
`request.META['wsgioauth2.session']`; in Flask it'll be
`flask.request['wsgioauth2.session']

This is a dict-like object with a couple of useful keys:

* `"username"` - the Heroku account email address (same as `env["REMOTE_USER"]`).

* `"access_token"` - the OAuth user access token. You can use this to
  [make authenticated requests](#making-requests) against the Heroku API.

<a name="making-requests"/>
## Making authenticated requests

Once you've got an authenticated user, you can make OAuth requests on their
behalf against the [Heroku Platform API](https://devcenter.heroku.com/articles/platform-api-quickstart).
The key is to set two HTTP headers:

* Set the `Authorization` header to `"Bearer: TOKEN"`, where `TOKEN` is the
  OAuth token found in `env["wsgioauth2.session"]["token"]`.

* Set the `Accept` header to `application/vnd.heroku+json; version=3` to
  select the "v3" API.

For details about Heroku API, see the
[getting started guide](https://devcenter.heroku.com/articles/platform-api-quickstart)
and the [Platform API reference](https://devcenter.heroku.com/articles/platform-api-reference).

For example, using [requests](http://python-requests.org/), you could create
a new app as the authenticated user using something like this:

```python
headers = {
    'Authorization': 'Bearer: %s' % environ['wsgioauth2.session']['token'],
    'Accept': 'application/vnd.heroku+json; version=3'
}
requests.post('https://api.heroku.com/apps', headers=headers)
```

<a name="options"/>
## Options

You can pass extra options as keyword arguments to `heroku_bouncer.bouncer()`.
Those options are:

* `set_remote_user` - if `True` (the default), then the Heroku username
  (which is also an email address) will end up on `environ["REMOTE_USER"]`.
  There's not a great reason to set this to `False`, but you can if you
  really feel like it I guess.

* `herokai_only` - `False` by default. If `True`, only allow logins from
  `@heroku.com` email addresses. You probably don't want this unless you
  work at Heroku.

* `path` - the path to use for the OAuth callback. This is the same path you'll
  pass to `heroku clients:create`; **note that it must end in a trailing
  slash!**. Defaults to ``/auth/heroku/callback/``, which you can probably
  leave alone unless that conflcits with a URL in your real app.

* `cookie` - name of the cookie to use. Defaults to `"herokuoauthsess"`.

*  `forbidden_path` - What path should be used to display the 403 Forbidden
   page. Any forbidden user will be redirected to this path and a default 403
   Forbidden page will be shown. To override the default  page see the next
   option.

* `forbidden_passthrough` - by default a generic 403 page will be generated. Set
  this to `True` to pass the request through to the protected application.

* `client_id` - the OAuth client ID. Read from `os.environ['HEROKU_OAUTH_ID']
  if not passed explicitly.

* `client_secret` - the OAuth client secret. Read from
  `os.environ['HEROKU_OAUTH_SECRET']` if not passed explicitly.

* `secret_key` - a secret key used to sign the session. Read from
  ``os.environ['SECRET_KEY']` if not passed explicitly.

<a name="flask"/>
## Integration with Flask

Hooking up with Flask is pretty simple; you'll just set `app.wsgi_app` following
[the example in the documentation](http://flask.pocoo.org/docs/quickstart/#hooking-in-wsgi-middlewares):

```python

import flask
import heroku_bouncer

app = flask.Flask(__name__)

#
# ... your app here ...
#

app.wsgi_app = heroku_bouncer.bouncer(app.wsgi_app)
```

<a name="django"/>
## Integration with Django

Integrating with Django's a bit more complex. First, you'll need to
[enable authentication against REMOTE_USER](https://docs.djangoproject.com/en/dev/howto/auth-remote-user/).
by adding `'django.contrib.auth.middleware.RemoteUserMiddleware'`
   to your ``MIDDLEWARE_CLASSES`` - make sure it's *after*
   `AuthenticationMiddleware`.

Then, you'll need to create a [remote user backend](https://docs.djangoproject.com/en/dev/howto/auth-remote-user/#remoteuserbackend) to map Heroku users to your users. At the very least,
you'll need to deal with the fact that Heroku uses emails for usernames and
Django doesn't. So a minimal remote user backend might look like this:

```python
import hashlib
from django.contrib.auth.backends import RemoteUserBackend

class HerokuRemoteUserBackend(RemoteUserBackend):
    create_unknown_user = True

    def clean_username(self, username):
        return hashlib.md5(username).hexdigest()
```

In practice, you may want to do something more complex (probably involving a
[custom user object](https://docs.djangoproject.com/en/dev/topics/auth/customizing
/#extending-the-existing-user-model)), including probably overriding
`configure_user()` as well to control initial permissions and such. See [the
docs for remote user authentication](https://docs.djangoproject.com/en/dev/howto
/auth-remote-user/#remoteuserbackend) for more details, as well as the more
general documentation on [customizing authentication](https://docs.djangoproject.com/en/dev/topics/auth/customizing/).

Once you've got your remote user backend, you'll need to add it to
`AUTHENTICATION_BACKENDS`:

```python
AUTHENTICATION_BACKENDS = ['myproject.auth.HerokuRemoteUserBackend']
```

Finally, you'll need to wire it up [as WSGI middleware in wsgi.py](https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/#applying-wsgi-middleware). Your final `wsgi.py` should look
something like:

```python
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "abuse.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import heroku_bouncer
application = heroku_bouncer.bouncer(application)
```

## Integration with other things

I don't know how to do other things! Please send me a pull request.

## Contributing

[Work happens on Github](http://github.com/heroku/heroku-bouncer-python).
Please send me a pull request!
