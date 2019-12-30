# Fork Features
* Disable SSL connection to Postgresql
* LDAP group member's from Microsoft Active Directory 

**Important: mapping group-cn must contain Distinguished Name(Cn=XX,ou=yyy,dc=abcd,dc=com)**

# gogs-groupsync
When run, this script synchronizes [LDAP](https://en.wikipedia.org/wiki/LDAP) groups with Teams within [Gogs](https://gogs.io) organizations. For this, the following is needed:

* Bind access to the LDAP server in order to query it for the members of each group.
* For each team to be synchornized, a Gogs API token with the access rights to add and remove team members (i.e., a token of one of the organization's owners). This token can be provided separately for each mapping.
* Due to limitations of the Gogs HTTP API (which as of May 2018 allows adding and removing team members but not listing the current members of a team), database credentials which allow read access to the Gogs database (only Postgresql is supported for now) are also needed. The database is queried for a list of current members of each team.

## Usage

First, create a [TOML](https://github.com/toml-lang/toml) configuration file. See `config.toml.example` for an example configuration, which synchronizes two LDAP groups with two teams within the Gogs organization `groupsync-test`.

Then, run

    $ ./groupsync.py <configfile>
    
You may need several Python dependencies, which you can install using

    $ pip install -r requirements.txt
    
Preferably, this should be done inside a virtualenv.

## Known limitations

* The need for Gogs DB credentials as mentioned above.
* While users who are team members in Gogs but not in the corresponding LDAP group are removed from the team on synchronization, they still stay members of the organization even if they no loger belong to any team. This might not be desired (as far as I know, these users cannot see or edit enything within the organization without a team, so this should be non-critcal).

Both of these restrictions are a result of the limited Gogs HTTP API. This will hopefully change in the furture (the Gitea API already includes the neccesary functionality).

* Currently, only a one-to-many mapping of LDAP groups to teams is possible. If two ore more LDAP groups are specified, the mapping specified later in the config file will overwrite the first one.

## License

    gogs-groupsync (Synchronize LDAP groups with Gogs teams)
    Copyright (C) 2018  Damian Hofmann

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
