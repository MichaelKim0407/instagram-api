from ._base import *

__author__ = 'Michael'


class ProfileAPI(BaseAPI):
    @post('accounts/change_password/')
    def profile_change_password(self, new_password):
        return None, {
            'old_password': self.password,
            'new_password1': new_password,
            'new_password2': new_password,
        }

    def profile_change_picture(self, photo):
        # TODO Instagram.php 705-775
        raise NotImplementedError()

    @post('accounts/remove_profile_picture/')
    def profile_remove_picture(self):
        pass

    @post('accounts/set_private/')
    def profile_set_private(self):
        pass

    @post('accounts/set_public/')
    def profile_set_public(self):
        pass

    @post('accounts/current_user/?edit=true')
    def profile_get_data(self):
        pass

    @post('accounts/edit_profile/')
    def profile_edit(self, url, phone, first_name, biography, email, gender):
        return None, {
            'external_url': url,
            'phone_number': phone,
            'username': self.username,
            'full_name': first_name,
            'biography': biography,
            'email': email,
            'gender': gender,
        }

    @post('accounts/set_phone_and_name/')
    def profile_set_contact(self, name='', phone=''):
        return None, {
            'first_name': name,
            'phone_number': phone,
        }
