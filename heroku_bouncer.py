import os
import wsgioauth2
import requests

def bouncer(application, set_remote_user=True, herokai_only=False,
            path='/auth/heroku/callback/', cookie='herokuoauthsess',
            forbidden_path='/auth/heroku/forbidden/', forbidden_passthrough=False,
            client_id=None, client_secret=None, secret_key=None):
    try:
        client_id = client_id or os.environ['HEROKU_OAUTH_ID']
        client_secret = client_secret or os.environ['HEROKU_OAUTH_SECRET']
        secret_key = secret_key or os.environ['SECRET_KEY']
    except KeyError as e:
        raise EnvironmentError("Missing configuration in environ: %s" % e)

    service = HerokuService(herokai_only=herokai_only)
    client = service.make_client(client_id=client_id, client_secret=client_secret)
    return client.wsgi_middleware(
        application = application,
        secret = secret_key,
        set_remote_user = set_remote_user,
        path = path,
        cookie = cookie,
        forbidden_path = forbidden_path,
        forbidden_passthrough = forbidden_passthrough
    )

class HerokuService(wsgioauth2.Service):
    def __init__(self, herokai_only=False):
        super(HerokuService, self).__init__(
            authorize_endpoint="https://id.heroku.com/oauth/authorize",
            access_token_endpoint="https://id.heroku.com/oauth/token")
        self.herokai_only = herokai_only

    def load_username(self, access_token):
        headers = {'Authorization': 'Bearer %s' % access_token,
                   'Accept': 'application/vnd.heroku+json; version=3'}
        resp = requests.get('https://api.heroku.com/account', headers=headers)
        access_token['username'] = resp.json()['email']

    def is_user_allowed(self, access_token):
        if self.herokai_only:
            return access_token['username'].endswith('@heroku.com')
        else:
            return True
