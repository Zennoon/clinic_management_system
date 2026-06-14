from django import forms
from django_enum.forms import EnumChoiceField
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings
from constance import config

from .models import Staff


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(
            {
                "class": "input input-bordered w-full focus:outline-indigo-600",
                "placeholder": "Username",
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            {
                "class": "input input-bordered w-full focus:outline-indigo-600",
                "placeholder": "********",
            }
        )
    )


class ClinicSettingsForm(forms.Form):
    app_title = forms.CharField(
        required=True,
        help_text=settings.CONSTANCE_CONFIG.get("APP_TITLE", ("", "Default help text"))[
            1
        ],
        widget=forms.TextInput(
            {
                "class": "input input-bordered",
            }
        ),
    )
    strict_mode = forms.BooleanField(
        required=False,
        help_text=settings.CONSTANCE_CONFIG.get(
            "STRICT_MODE", ("", "Default help text")
        )[1],
        widget=forms.CheckboxInput({"class": "toggle"}),
    )
    consultation_fee = forms.DecimalField(
        min_value=0,
        help_text=settings.CONSTANCE_CONFIG.get(
            "CONSULTATION_FEE", ("", "Default help text")
        )[1],
        widget=forms.NumberInput(
            {"class": "input input-bordered", "placeholder": "Consultation Fee"}
        ),
    )
    grace_period = forms.IntegerField(
        min_value=0,
        help_text=settings.CONSTANCE_CONFIG.get(
            "FOLLOW_UP_GRACE_DAYS", ("", "Default help text")
        )[1],
        widget=forms.NumberInput(
            {
                "class": "input input-bordered",
                "placeholder": "Grace Period (Number of days)",
            }
        ),
    )
    allow_charge_bypass = forms.BooleanField(
        required=False,
        help_text=settings.CONSTANCE_CONFIG.get(
            "ALLOW_CHARGE_BYPASS", ("", "Default help text")
        )[1],
        widget=forms.CheckboxInput({"class": "toggle"}),
    )
    require_partial_payment = forms.BooleanField(
        required=False,
        help_text=settings.CONSTANCE_CONFIG.get(
            "REQUIRE_PARTIAL_PAYMENT", ("", "Default help text")
        )[1],
        widget=forms.CheckboxInput({"class": "toggle"}),
    )
    partial_payment_percent = forms.DecimalField(
        required=False,
        help_text=settings.CONSTANCE_CONFIG.get(
            "PARTIAL_PAYMENT_PERCENT", ("", "Default help text")
        )[1],
        min_value=1,
        max_value=100,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["app_title"].initial = config.APP_TITLE
        self.fields["strict_mode"].initial = config.STRICT_MODE
        self.fields["consultation_fee"].initial = config.CONSULTATION_FEE
        self.fields["grace_period"].initial = config.FOLLOW_UP_GRACE_DAYS
        self.fields["allow_charge_bypass"].initial = config.ALLOW_CHARGE_BYPASS
        self.fields["require_partial_payment"].initial = (
            config.ALLOW_CHARGE_BYPASS and config.REQUIRE_PARTIAL_PAYMENT
        )
        self.fields["partial_payment_percent"].initial = (
            config.ALLOW_CHARGE_BYPASS and config.PARTIAL_PAYMENT_PERCENT
        )

    def save_settings(self):
        config.APP_TITLE = self.cleaned_data.get("app_title", config.APP_TITLE)
        config.STRICT_MODE = self.cleaned_data.get("strict_mode", config.STRICT_MODE)
        config.CONSULTATION_FEE = self.cleaned_data.get(
            "consultation_fee", config.CONSULTATION_FEE
        )
        config.FOLLOW_UP_GRACE_DAYS = self.cleaned_data.get(
            "grace_period", config.FOLLOW_UP_GRACE_DAYS
        )
        config.ALLOW_CHARGE_BYPASS = self.cleaned_data.get(
            "allow_charge_bypass", config.ALLOW_CHARGE_BYPASS
        )
        config.REQUIRE_PARTIAL_PAYMENT = self.cleaned_data.get(
            "require_partial_payment", config.REQUIRE_PARTIAL_PAYMENT
        )
        config.PARTIAL_PAYMENT_PERCENT = self.cleaned_data.get(
            "partial_payment_percent", config.PARTIAL_PAYMENT_PERCENT
        )


class StaffForm(forms.ModelForm):
    email = forms.CharField(
        widget=forms.TextInput(
            {"class": "input input-bordered w-full", "placeholder": "Email Address"}
        ),
        required=False,
    )
    username = forms.CharField(
        widget=forms.TextInput(
            {"class": "input input-bordered w-full", "placeholder": "Username"}
        ),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            {"class": "input input-bordered w-full", "placeholder": "Password"}
        ),
    )
    phone = forms.CharField(
        widget=forms.TextInput(
            {"class": "input input-bordered w-full", "placeholder": "Phone number"}
        ),
        required=False,
    )
    address = forms.CharField(
        widget=forms.TextInput(
            {"class": "input input-bordered w-full", "placeholder": "Address"}
        ),
        required=False,
    )
    role = EnumChoiceField(
        enum=Staff.RoleEnum,
        choices=[(tag.value, tag.label) for tag in Staff.RoleEnum],
        required=True,
        widget=forms.Select(
            {
                "class": "select select-bordered",
                "placeholder": "Select the role of new user",
            }
        ),
    )
    date = forms.DateTimeField(
        initial=timezone.now().date(),
        widget=forms.DateInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Date",
                "type": "date",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        is_update = self.instance and self.instance.pk
        self._original_password = self.instance.password
        self.fields["password"].required = not is_update

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if (
            Staff.objects.exclude(id=self.initial.get("id"))
            .filter(email=email)
            .exists()
        ):
            raise ValidationError(f"The email {email} is already in use.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if (
            Staff.objects.exclude(id=self.initial.get("id"))
            .filter(username=username)
            .exists()
        ):
            raise ValidationError(f"The username {username} is already in use.")
        return username

    def save(self, commit=True):
        staff = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            staff.set_password(password)
        elif self.instance.pk:
            staff.password = self._original_password

        if commit:
            staff.save()

        return staff

    class Meta:
        model = Staff
        fields = {"email", "username", "password", "phone", "address", "role", "date"}
