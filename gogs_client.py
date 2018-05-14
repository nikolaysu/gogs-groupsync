import contextlib
import psycopg2 as pg
from psycopg2.extras import LoggingConnection
import requests

from common import GroupsyncError

class GogsApiClient:
    def __new__(cls, *args, **kwargs):
        obj = super(GogsApiClient, cls).__new__(cls)
        obj.__init__(*args, **kwargs)
        return contextlib.closing(obj)

    def __init__(self, base_url, db_config, logger):
        self.base_url = base_url
        self.pg_conn = pg.connect(
            dbname=db_config['name'],
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            connection_factory=LoggingConnection)
        self.pg_conn.initialize(logger)

    def close(self):
        self.pg_conn.close()

    def get_teams_for_org(self, org_name, token):
        path = '/orgs/{}/teams'.format(org_name)
        try:
            response = requests.get(self.base_url + path, headers={
                'Authorization': 'token {}'.format(token),
            })
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise GroupsyncError("GOGS: Failed to get teams for org '{}': {}".format(org_name, e))

    TEAM_MEMBER_QUERY = 'select u.name from "user" u, team_user tu where u.id = tu.uid and tu.team_id = %s;'
    def get_team_members(self, team_id):
        try:
            with self.pg_conn.cursor() as cur:
                cur.execute(self.TEAM_MEMBER_QUERY, (team_id,))
                return [uid[0] for uid in cur]
        except Exception as e:
            raise GroupsyncError("GOGS:DB: Failed to retrieve members of team {}: {}".format(team_id, e))

    def add_user_to_team(self, team_id, username, token):
        path = '/admin/teams/{}/members/{}'.format(team_id, username)
        try:
            response = requests.put(self.base_url + path, headers={
                'Authorization': 'token {}'.format(token),
            })
            if response.status_code == 404: # no such user
                return False
            response.raise_for_status()
        except Exception as e:
            raise GroupsyncError("GOGS: Failed to add {} to team: {}".format(username, e))
        return True

    def remove_user_from_team(self, team_id, username, token):
        path = '/admin/teams/{}/members/{}'.format(team_id, username)
        try:
            response = requests.delete(self.base_url + path, headers={
                'Authorization': 'token {}'.format(token),
            })
            if response.status_code == 404: # no such user
                return False
            response.raise_for_status()
        except Exception as e:
            raise GroupsyncError("GOGS: Failed to remove {} from team: {}".format(username, e))
        return True

    ORG_MEMBER_QUERY = '''
        select u.name
        from "user" u, org_user ou
        where u.id = ou.uid and ou.org_id = %s;
    '''
    def get_org_members(self, org_id):
        try:
            with self.pg_conn.cursor() as cur:
                cur.execute(self.ORG_MEMBER_QUERY, (org_id,))
                return [uid[0] for uid in cur]
        except Exception as e:
            raise GroupsyncError("GOGS:DB: Failed to retrieve members of team {}: {}".format(team_id, e))

    ORG_ID_QUERY = 'SELECT id from "user" where type=1 and name=%s'
    def get_org_id(self, org_name):
        with self.pg_conn.cursor() as cur:
            cur.execute(self.ORG_ID_QUERY, (org_name,))
            return cur.fetchone()[0]

    UID_QUERY = 'SELECT id from "user" where type=0 and name=%s'
    def get_user_id(self, username):
        with self.pg_conn.cursor() as cur:
            cur.execute(self.UID_QUERY, (username,))
            result = cur.fetchone()
            if result:
                return result[0] # <- uid
            else:
                return None
