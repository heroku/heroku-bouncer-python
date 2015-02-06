from werkzeug import testapp
from werkzeug.test import create_environ, run_wsgi_app
from heroku_bouncer import bouncer

def test_bouncer():
    app = bouncer(testapp.test_app, client_id='CID', client_secret='CS', secret_key='SKEY')
    env = create_environ()
    app_iter, status, headers = run_wsgi_app(app, env)
    assert status == '307 Temporary Redirect'
    assert headers['Location'].startswith('https://id.heroku.com/')

