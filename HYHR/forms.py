from django import forms
from django.contrib.auth.admin import User

from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _
from django.forms import ModelForm

from datetime import datetime, date
from django.utils import timezone
from django.contrib.admin.widgets import AdminDateWidget

class BootstrapAuthenticationForm(AuthenticationForm):
    """Authentication form which uses boostrap CSS."""
    username = forms.CharField(max_length=254,
                               widget=forms.TextInput({
                                   'class': 'form-control',
                                   'placeholder': 'User name'}))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput({
                                   'class': 'form-control',
                                   'placeholder':'Password'}))


class RegisterForm(forms.Form):
    username = forms.SlugField(required=True, max_length=100)
    password = forms.CharField(required=True, widget=forms.PasswordInput, min_length=8, max_length=15)
    confirm_password = forms.CharField(required=True, widget=forms.PasswordInput, min_length=8, max_length=15)

    realname = forms.CharField(max_length=100, required=True)
    pid = forms.CharField(max_length=18, required=True)
    phoneNo = forms.CharField(max_length=11, required=True, help_text='phone No')
    comment = forms.CharField(max_length=100, required=False)

    def clean(self):
        cd = super(RegisterForm,self).clean()
        pswd = cd.get('password','password')
        cpswd = cd.get('confirm_password','confirm_password')
        if pswd != cpswd:
            raise forms.ValidationError('Passwords not match.')
        return cd

    def clean_pid(self):
        id = self.cleaned_data.get('pid','')
        if len(id) != 18 and len(id) != 15:
            raise forms.ValidationError('invalid pid length. it should be either length 15 or 18')
        elif len(id) == 15 and not id.isnumeric():
            raise forms.ValidationError('pid with length 15 should be numeric.')
        elif len(id) == 18:
            if not id[:17].isnumeric() or (id[-1].upper() != 'X' and not id[-1].isnumeric()):
                raise forms.ValidationError('pid with length 18 should be numeric or end with X.')      
        return id


    def clean_phoneNo(self):
        pno = self.cleaned_data.get('phoneNo', '')
        if not len(pno) == 11 or not pno.isnumeric():
            raise forms.ValidationError('Invalid Phone NO of China, it should be numeric and with length 11.')
        return pno

    def clean_username(self):

        try:
            name = self.cleaned_data.get('username','')
            exist = User.objects.filter(username__iexact=name).exists()
        except Exception:
            raise forms.ValidationError('cannot validate the user name')
        if exist:
            raise forms.ValidationError('User name already exists')     
        return name


    def clean_password(self):
        pswd = self.cleaned_data.get('password','')
        if len(pswd)<8:
            raise forms.ValidationError('password too short.')
        return pswd

    def clean_confirm_password(self):
        pswd = self.cleaned_data.get('confirm_password', '')
        if len(pswd) < 8:
            raise forms.ValidationError('password too short.')
        return pswd
