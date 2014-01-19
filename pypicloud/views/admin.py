""" API endpoints for admin controls """
from pypicloud.route import AdminResource
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.view import view_config, view_defaults

from pyramid_duh import argify


@view_defaults(context=AdminResource, subpath=(), permission='admin',
               renderer='json')
class AdminEndpoints(object):

    """ Collection of admin endpoints """

    def __init__(self, request):
        self.request = request

    @view_config(name='rebuild')
    def rebuild_package_list(self):
        """ Rebuild the package cache in the database """
        self.request.db.reload_from_storage()
        return self.request.response

    @view_config(name='pending_users', request_method='GET')
    def get_pending_users(self):
        """ Get the list of pending users """
        return self.request.access.pending_users()

    @view_config(name='user', request_method='GET')
    def get_users(self):
        """ Get the list of users """
        return self.request.access.user_data()

    @view_config(name='user', subpath=('username/*'), request_method='GET')
    def get_user(self):
        """ Get a single user """
        username = self.request.named_subpaths['username']
        return self.request.access.user_data(username)

    @view_config(name='user', subpath=('username/*'), request_method='DELETE')
    def delete_users(self):
        """ Delete a user """
        username = self.request.named_subpaths['username']
        self.request.access.delete_user(username)
        return self.request.response

    @view_config(name='user', subpath=('username/*', 'approve'),
                 request_method='POST')
    def approve_user(self):
        """ Approve a pending user """
        username = self.request.named_subpaths['username']
        self.request.access.approve_user(username)
        return self.request.response

    @view_config(name='user', subpath=('username/*', 'admin'),
                 request_method='POST')
    @argify
    def set_admin_status(self, admin):
        """ Approve a pending user """
        username = self.request.named_subpaths['username']
        self.request.access.set_user_admin(username, admin)
        return self.request.response

    @view_config(name='user', subpath=('username/*', 'group', 'group/*'),
                 request_method='PUT')
    def add_user_to_group(self):
        """ Add a user to a group """
        username = self.request.named_subpaths['username']
        group = self.request.named_subpaths['group']
        self.request.access.edit_user_group(username, group, True)
        return self.request.response

    @view_config(name='user', subpath=('username/*', 'group', 'group/*'),
                 request_method='DELETE')
    def remove_user_from_group(self):
        """ Remove a user from a group """
        username = self.request.named_subpaths['username']
        group = self.request.named_subpaths['group']
        self.request.access.edit_user_group(username, group, False)
        return self.request.response

    @view_config(name='group', request_method='GET')
    def get_groups(self):
        """ Get the list of groups """
        return self.request.access.groups()

    @view_config(name='group', subpath=('group/*'), request_method='DELETE')
    def delete_group(self):
        """ Delete a group """
        group = self.request.named_subpaths['group']
        self.request.access.delete_group(group)
        return self.request.response

    @view_config(name='user', subpath=('username/*', 'permissions'))
    def get_user_permissions(self):
        """ Get the package permissions for a user """
        username = self.request.named_subpaths['username']
        return self.request.access.user_package_permissions(username)

    @view_config(name='group', subpath=('group/*'))
    def get_group_permissions(self):
        """ Get the package permissions for a group """
        group = self.request.named_subpaths['group']
        return {
            'members': self.request.access.group_members(group),
            'packages': self.request.access.group_package_permissions(group),
        }

    @view_config(name='package', subpath=('package/*'))
    def get_package_permissions(self):
        """ Get the user and group permissions set on a package """
        package = self.request.named_subpaths['package']
        user_perms = [{'username': key, 'permissions': val} for key, val in
                      self.request.access.user_permissions(package).iteritems()]
        group_perms = [{'group': key, 'permissions': val} for key, val in
                       self.request.access.group_permissions(package).iteritems()]
        return {
            'user': user_perms,
            'group': group_perms,
        }

    @view_config(name='group', subpath=('group/*'), request_method='PUT')
    def create_group(self):
        """ Create a group """
        group = self.request.named_subpaths['group']
        if group in ('everyone', 'authenticated'):
            raise HTTPBadRequest("'%s' is a reserved name" % group)
        self.request.access.create_group(group)
        return self.request.response

    @view_config(name='package',
                 subpath=('package/*', 'type/user|group/r',
                          'name/*', 'permission/read|write/r'),
                 request_method='PUT')
    @view_config(name='package',
                 subpath=('package/*', 'type/user|group/r',
                          'name/*', 'permission/read|write/r'),
                 request_method='DELETE')
    def edit_permission(self):
        """ Edit user permission on a package """
        package = self.request.named_subpaths['package']
        name = self.request.named_subpaths['name']
        permission = self.request.named_subpaths['permission']
        owner_type = self.request.named_subpaths['type']
        if owner_type == 'user':
            self.request.access.edit_user_permission(package, name, permission,
                                                     self.request.method == 'PUT')
        else:
            self.request.access.edit_group_permission(
                package, name, permission,
                self.request.method == 'PUT')
        return self.request.response

    @view_config(name='register', request_method='POST')
    @argify
    def toggle_allow_register(self, allow):
        """ Allow or disallow user registration """
        self.request.access.set_allow_register(allow)
        return self.request.response