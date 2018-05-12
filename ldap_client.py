import ldap
from common import GroupsyncError


class LdapClient:
    GROUP_SEARCH_FILTER = '(&(cn={cn})(objectClass=posixGroup))'

    def __init__(self, server, bind_dn, password, group_base_dn):
        self.server = server
        self.conn = ldap.initialize(server)
        self.group_base_dn = group_base_dn
        
        try:
            self.conn.protocol_version = ldap.VERSION3
            self.conn.simple_bind_s(bind_dn, password)
        except Exception as e:
            raise GroupsyncError("LDAP: Could not connect to '{}': {}".format(server, e))

    def get_group_members(self, group_cn):
        try:
            result_id = self.conn.search(
                base=self.group_base_dn,
                scope=ldap.SCOPE_SUBTREE,
                filterstr=self.GROUP_SEARCH_FILTER.format(cn=group_cn))

            results = []
            while 1:
                kind, data = self.conn.result(result_id, 0)
                if data == []:
                    break
                else:
                    if kind == ldap.RES_SEARCH_ENTRY:
                        results.append(data)

            return results[0][0][1]['memberUid']
        except Exception as e:
            raise GroupsyncError("LDAP: Failed to lookup group '{}' at '{}': {}".format(group_cn, self.server, e))
