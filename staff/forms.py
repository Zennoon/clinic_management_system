from django import forms

from .models import Staff

class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput({
            "class": "input input-bordered w-full dark:bg-white/5 focus:outline-indigo-600 dark:focus:outline-indigo-500 dark:text-white",
            "placeholder": "Username"
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput({
            "class": "input input-bordered w-full dark:bg-white/5 focus:outline-indigo-600 dark:focus:outline-indigo-500 dark:text-white",
            "placeholder": "********"
        })
    )