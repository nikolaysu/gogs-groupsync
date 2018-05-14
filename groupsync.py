#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import click
import click_log
import logging
import sys
import toml

from common import GroupsyncError
from ldap_client import LdapClient
from gogs_client import GogsApiClient


logger = logging.getLogger(__name__)
click_log.basic_config(logger)


class Mapping:
    def __init__(self, dict):
        self.cn = dict['ldap']['group-cn']
        self.target_org = dict['gogs']['org']
        self.target_team = dict['gogs'].get('team', None)
        self.auth_token = dict['gogs']['auth-token']
        self.is_public = dict['gogs'].get('is_public', False)
        self.is_owner = dict['gogs'].get('is_owner', False)

        self.type = 'team' if self.target_team else 'org'

        self.target = f"{self.target_org}/{self.target_team}"

    def __str__(self):
        if self.type == 'team':
            return f"{self.cn}->{self.target_org}/{self.target_team}"
        elif self.type == 'org':
            return f"{self.cn}->{self.target_org}"


def process_mapping(mapping, ldap, gogs):
    if mapping.type == 'team':
        sync_team(mapping, ldap, gogs)
    elif mapping.type == 'org':
        sync_org(mapping, ldap, gogs)
    else:
        raise GroupsyncError(f"Illegal mapping type {mapping.type}")


def sync_team(mapping, ldap, gogs):
    logger.info(mapping)

    ldap_group_members = set([
        username.decode('utf-8') for username in ldap.get_group_members(mapping.cn)
    ])
    if not len(ldap_group_members):
        raise GroupsyncError("LDAP: Empty group")

    teams = [team for team in gogs.get_teams_for_org(mapping.target_org, mapping.auth_token)
             if team['name'] == mapping.target_team]
    if len(teams) != 1:
        raise GroupsyncError(f"GOGS: Could not find team {mapping.target}")
    team_id = teams[0]['id']

    current_members = set(gogs.get_team_members(team_id))
    users_to_add = ldap_group_members.difference(current_members)
    users_to_remove = current_members.difference(ldap_group_members)

    logger.debug(f"\tcurrent: {current_members}")
    logger.debug(f"\tto_add: {users_to_add}")
    logger.debug(f"\tto_rem: {users_to_remove}")
    for username in users_to_add:
        res = gogs.add_user_to_team(team_id, username, mapping.auth_token)
        if res:
            logger.info(f'\tADD      {username}')
        else:
            logger.info(f'\tSKIP ADD {username}')
    for username in users_to_remove:
        res = gogs.remove_user_from_team(team_id, username, mapping.auth_token)
        if res:
            logger.info(f'\tDEL      {username}')
        else:
            logger.info(f'\tSKIP DEL {username}')


def sync_org(mapping, ldap, gogs):
    logger.info(mapping)
    logger.warning("Organization sync not yet implemented")
    return

    ldap_group_members = set([
        username.decode('utf-8') for username in ldap.get_group_members(mapping.cn)
    ])
    if not len(ldap_group_members):
        raise GroupsyncError("LDAP: Empty group")

    org_id = gogs.get_org_id(mapping.target_org)

    current_members = set(gogs.get_org_members(org_id))
    users_to_remove = current_members.difference(ldap_group_members)

    for username in users_to_remove:
        uid = gogs.get_user_id(username)
        if uid:
            gogs.remove_user_from_org(org_id, uid)
            logger.info(f'\tDEL      {username}')
        else:
            logger.info(f'\tSKIP DEL {username}')


@click.command()
@click.argument('config_filename')
@click_log.simple_verbosity_option(logger)
def main(config_filename):
    config = toml.load(config_filename)

    ldap = LdapClient(
        server=config['ldap']['server'],
        bind_dn=config['ldap']['bind-dn'],
        password=config['ldap']['password'],
        group_base_dn=config['ldap']['group-base-dn'])

    with GogsApiClient(
            base_url=config['gogs']['base-url'],
            db_config=config['gogs']['db'],
            logger=logger) as gogs:

        mappings = []
        for mdict in config['mapping']:
            try:
                mapping = Mapping(mdict)
                mappings.append(mapping)
            except KeyError as e:
                logger.warning(f"Skipping {mapping}:\n\t{e}")
                continue

        for mapping in sorted(mappings, key=lambda m: m.type, reverse=True):
            try:
                process_mapping(mapping, ldap, gogs)
            except GroupsyncError as e:
                logger.warning(f"Skipping {mapping}:\n\t{e}")

if __name__ == "__main__":
    main()
