from ._base import *

__author__ = 'Michael'


class ProfileAPI(BaseAPI):
    @post('accounts/change_password/')
    def change_password(self, new_password):
        return None, {
            'old_password': self.password,
            'new_password1': new_password,
            'new_password2': new_password,
        }

    def change_profile_picture(self, photo):
        # TODO Instagram.php 705-775
        raise NotImplementedError()

    @post('accounts/remove_profile_picture/')
    def remove_profile_picture(self):
        pass

    @post('accounts/set_private/')
    def set_private_account(self):
        pass

    @post('accounts/set_public/')
    def set_public_account(self):
        pass

    @post('accounts/current_user/?edit=true')
    def get_profile_data(self):
        pass

    @post('accounts/edit_profile/')
    def edit_profile(self, url, phone, first_name, biography, email, gender):
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
    def set_name_and_phone(self, name='', phone=''):
        return None, {
            'first_name': name,
            'phone_number': phone,
        }
