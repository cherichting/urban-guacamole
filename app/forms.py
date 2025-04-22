"""
Definition of forms.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _


class BootstrapAuthenticationForm(AuthenticationForm):
    """Authentication form which uses boostrap CSS."""
    username = forms.CharField(max_length=254,
                               widget=forms.TextInput({
                                   'class': 'form-control',
                                   'placeholder': 'User name'}))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput({
                                   'class': 'form-control',
                                   'placeholder': 'Password'}))


class RegsiterForm(forms.Form):
    """Authentication form which uses boostrap CSS."""
    username = forms.CharField(max_length=254,
                               widget=forms.TextInput({
                                   'class': 'form-control',
                                   'placeholder': '用户名'}))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput({
                                   'class': 'form-control',
                                   'placeholder': '密码'}))
    password2 = forms.CharField(label=_("Password2"),
                                widget=forms.PasswordInput({
                                    'class': 'form-control',
                                    'placeholder': '确认密码'}))
    user_type = forms.CharField(label="用户类型",
                                  widget=forms.TextInput({
                                      'class': 'form-control',
                                      'placeholder': '用户类型'}),
                                  )
    class_name = forms.CharField(label="班级",
                                   widget=forms.TextInput({
                                       'class': 'form-control',
                                       'placeholder': '班级'}),
                                   )
