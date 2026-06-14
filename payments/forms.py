from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django_enum.forms import EnumChoiceField
from dynamic_forms import DynamicField, DynamicFormMixin

from charges.models import Charge
from patients.models import Patient
from staff.models import Staff
from visits.models import Visit
from payments.models import Adjustment, Payment


class PaymentForm(DynamicFormMixin, forms.ModelForm):
    def initial_patient(self=None):
        if self and self.instance.pk:
            return self.instance.charge.visit.patient
        return Patient.objects.exclude(is_active=False).order_by("first_name").first()

    def visit_choices(self):
        patient = self["patient"].value()
        return (
            Visit.objects.exclude(is_active=False)
            .filter(patient=patient)
            .filter(charges__isnull=False)
            .distinct()
            .order_by("-date")
        )

    def initial_visit(self):
        if self.instance.pk:
            return self.instance.charge.visit
        patient = self["patient"].value()
        return (
            Visit.objects.exclude(is_active=False)
            .filter(patient=patient)
            .order_by("-date")
            .first()
        )

    def charge_choices(self):
        visit = self["visit"].value()
        return (
            Charge.objects.exclude(is_active=False)
            .filter(visit=visit)
            .order_by("-date")
        )

    def initial_charge(self):
        if self.instance.pk:
            return self.instance.charge
        visit = self["visit"].value()
        return Charge.objects.filter(visit=visit).order_by("-date").first()

    patient = forms.ModelChoiceField(
        Patient.objects.exclude(is_active=False)
        .filter(visits__isnull=False)
        .distinct()
        .order_by("first_name"),
        required=True,
        empty_label="Select a patient",
        initial=initial_patient,
        widget=forms.Select(
            attrs={
                "class": "select select-bordered w-full",
            }
        ),
    )

    visit = DynamicField(
        forms.ModelChoiceField,
        queryset=visit_choices,
        initial=initial_visit,
        required=True,
    )

    charge = DynamicField(
        forms.ModelChoiceField,
        queryset=Charge.objects,
        required=True,
        empty_label="Select a charge",
        widget=forms.Select(attrs={"class": "select select-bordered w-full"}),
    )

    amount = forms.DecimalField(
        min_value=0.0,
        required=True,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Amount",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )

    payment_method = EnumChoiceField(
        enum=Payment.PaymentMethodEnum,
        choices=map(
            lambda choice: (choice.value, choice.label),
            Payment.selectable_payment_methods(),
        ),
        required=True,
        widget=forms.Select(
            attrs={
                "class": "select select-bordered w-full",
            }
        ),
    )

    date = forms.DateTimeField(
        initial=timezone.now().date,
        widget=forms.DateInput(
            attrs={"class": "input input-bordered w-full", "type": "date"}
        ),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if not hasattr(self, "cleaned_data"):
            self.cleaned_data = {}

        if self.user and self.user.role == Staff.RoleEnum.ADMIN:
            self.fields.get("payment_method").choices = (
                Payment.PaymentMethodEnum.choices
            )

        self.fields.get("charge").queryset = self.charge_choices()
        self.fields.get("charge").initial = self.initial_charge()

        if self.instance.pk and not (
            self.user and self.user.role == Staff.RoleEnum.ADMIN
        ):
            self.fields.get("patient").widget = forms.TextInput({
                "class": "input input-bordered",
                "readonly": "true"
            })
            self.fields.get("visit").widget = forms.TextInput({
                "class": "input input-bordered",
                "readonly": "true"
            })
            self.fields.get("charge").widget = forms.TextInput({
                "class": "input input-bordered",
                "readonly": "true"
            })
            self.fields.get("amount").widget = forms.TextInput({
                "class": "input input-bordered",
                "readonly": "true"
            })
            self.fields.get("date").widget = forms.TextInput({
                "class": "input input-bordered",
                "readonly": "true"
            })

            if self.instance.payment_method not in Payment.selectable_payment_methods():
                self.fields.get("payment_method").choices = (
                    Payment.PaymentMethodEnum.choices
                )
                for field in self.fields.values():
                    field.disabled = True
                self.disable_submit = True
                self.add_error(
                    None, "You are not authorized to modify system generated payments."
                )

    def clean_patient(self):
        if self.instance and not (self.user and self.user.role == Staff.RoleEnum.ADMIN):
            return self.instance.charge.visit.patient
        patient = self.cleaned_data.get("patient")
        if patient and not patient.is_operational:
            self.add_error(
                "patient",
                "This patient is archived, and cannot be modified. Please contact an admin to get them restored.",
            )

        return patient

    def clean_visit(self):
        if self.instance and not (self.user and self.user.role == Staff.RoleEnum.ADMIN):
            return self.instance.charge.visit
        visit = self.cleaned_data.get("visit")
        if visit and not visit.is_operational:
            self.add_error(
                "visit",
                "This visit is archived, and cannot be modified. Please contact an admin to get it restored.",
            )

        return visit

    def clean_charge(self):
        if self.instance and not (self.user and self.user.role == Staff.RoleEnum.ADMIN):
            return self.instance.charge
        charge = self.cleaned_data.get("charge")
        if charge and not charge.is_operational:
            self.add_error(
                "charge",
                "This charge is archived, and cannot be modified. Please contact an admin to get it restored.",
            )

        return charge

    def clean_amount(self):
        if self.instance and not (self.user and self.user.role == Staff.RoleEnum.ADMIN):
            return self.instance.date
        amount = self.cleaned_data.get("amount")
        if amount <= 0:
            self.add_error("amount", "Please enter an amount greater than 0.")

    def clean_date(self):
        if self.instance and not (self.user and self.user.role == Staff.RoleEnum.ADMIN):
            return self.instance.date
        date = self.cleaned_data.get("date")
        charge = self.cleaned_data.get("charge")
        if date.date() > timezone.now().date():
            raise ValidationError(
                "Payments cannot be scheduled for future dates.",
            )
        if charge and date.date() < charge.date.date():
            raise ValidationError(
                f"Payments cannot be paid before the charge date ({charge.date.date()}).",
            )
        source_date = self.instance.date if self.instance else timezone.now()
        if source_date:
            date = date.replace(
                hour=source_date.hour,
                minute=source_date.minute,
                second=source_date.second,
                microsecond=source_date.microsecond,
            )
        return date

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.pk and not self.instance.is_operational:
            self.add_error(None, "Changes to archived payment cannot be saved")
            return cleaned_data
        if not (self.user and self.user.role == Staff.RoleEnum.ADMIN) and (
            self.instance.pk
            and self.instance.payment_method not in Payment.selectable_payment_methods()
        ):
            self.add_error(
                None, "You are not authorized to modify system generated payments."
            )
            return cleaned_data  
        amount = cleaned_data.get("amount")
        charge = cleaned_data.get("charge")
        if amount and charge and amount > charge.net_balance:
            self.add_error(
                "amount",
                f"Selected charge has an unpaid amount of {max(charge.net_balance, Decimal("0.00"))}",
            )
        return cleaned_data

    class Meta:
        model = Payment
        fields = ["charge", "amount", "payment_method", "date"]


class ChargePaymentForm(DynamicFormMixin, forms.ModelForm):
    amount = forms.DecimalField(
        min_value=0.0,
        required=True,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Amount",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )

    payment_method = EnumChoiceField(
        enum=Payment.PaymentMethodEnum,
        choices=map(
            lambda choice: (choice.value, choice.label),
            Payment.selectable_payment_methods(),
        ),
        required=True,
        widget=forms.Select(
            attrs={
                "class": "select select-bordered w-full",
            }
        ),
    )

    date = forms.DateTimeField(
        initial=timezone.now().date,
        widget=forms.DateInput(
            attrs={"class": "input input-bordered w-full", "type": "date"}
        ),
    )

    def __init__(self, *args, user=None, charge=None, **kwargs):
        self.user = user
        self.charge = charge
        super().__init__(*args, **kwargs)

        if not hasattr(self, "cleaned_data"):
            self.cleaned_data = {}

        if self.instance.pk:
            msg = "Please use the update form for updates."
            self.add_error(None, msg)
            for field in self.fields.values():
                field.disabled = True
            self.disable_submit = True

        if charge and not charge.is_operational:
            msg = "This charge is archived, and cannot be modified. Please contact an admin to get it restored."
            self.add_error(None, msg)
            for field in self.fields.values():
                field.disabled = True
            self.disable_submit = True

        if self.user and self.user.role == Staff.RoleEnum.ADMIN:
            self.fields.get("payment_method").choices = (
                Payment.PaymentMethodEnum.choices
            )

    def clean_date(self):
        date = self.cleaned_data.get("date")
        if date.date() > timezone.now().date():
            raise ValidationError(
                "Payments cannot be scheduled for future dates.",
            )
        if self.charge and date.date() < self.charge.date.date():
            raise ValidationError(
                f"Payments cannot be paid before the charge date ({self.charge.date.date()}).",
            )
        source_date = self.instance.date if self.instance else timezone.now()
        if source_date:
            date = date.replace(
                hour=source_date.hour,
                minute=source_date.minute,
                second=source_date.second,
                microsecond=source_date.microsecond,
            )
        return date

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.pk and not self.instance.is_operational:
            self.add_error(None, "Changes to archived payment cannot be saved")
            return cleaned_data
        if not self.charge.is_operational:
            self.add_error(None, "Changes to archived charge cannot be saved")
            return cleaned_data
        amount = cleaned_data.get("amount")
        if amount and amount > self.charge.net_balance:
            self.add_error(
                "amount",
                f"Charge has an unpaid amount of {max(self.charge.net_balance, Decimal("0.00"))}",
            )

        return cleaned_data

    class Meta:
        model = Payment
        fields = ["amount", "payment_method", "date"]


class VisitPaymentForm(DynamicFormMixin, forms.ModelForm):
    def charge_choices(self):
        visit = self.visit or None
        return (
            Charge.objects.exclude(is_active=False)
            .filter(visit=visit)
            .order_by("-date")
        )

    def initial_charge(self):
        if self.instance.pk:
            return self.instance.charge

        visit = self.visit or None
        return (
            Charge.objects.exclude(is_active=False)
            .filter(visit=visit)
            .order_by("-date")
            .first()
        )

    charge = forms.ModelChoiceField(
        queryset=Charge.objects.exclude(is_active=False).order_by("-date").all(),
        required=True,
        empty_label="Select a charge",
        widget=forms.Select(
            attrs={
                "class": "select select-bordered w-full",
            }
        ),
    )

    amount = forms.DecimalField(
        min_value=0.0,
        required=True,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Amount",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )

    payment_method = EnumChoiceField(
        enum=Payment.PaymentMethodEnum,
        choices=map(
            lambda choice: (choice.value, choice.label),
            Payment.selectable_payment_methods(),
        ),
        required=True,
        widget=forms.Select(
            attrs={
                "class": "select select-bordered w-full",
            }
        ),
    )

    date = forms.DateTimeField(
        initial=timezone.now().date,
        widget=forms.DateInput(
            attrs={"class": "input input-bordered w-full", "type": "date"}
        ),
    )

    def __init__(self, *args, visit=None, user=None, **kwargs):
        self.visit = visit
        self.user = user
        super().__init__(*args, **kwargs)

        if not hasattr(self, "cleaned_data"):
            self.cleaned_data = {}

        if self.instance.pk:
            msg = "Please use the update form for updates."
            self.add_error(None, msg)
            for field in self.fields.values():
                field.disabled = True
            self.disable_submit = True

        if visit and not visit.is_operational:
            msg = "This visit is archived, and cannot be modified. Please contact an admin to get it restored."
            self.add_error(None, msg)
            for field in self.fields.values():
                field.disabled = True
            self.disable_submit = True

        if self.user and self.user.role == Staff.RoleEnum.ADMIN:
            self.fields.get("payment_method").choices = (
                Payment.PaymentMethodEnum.choices
            )

        self.fields.get("charge").queryset = self.charge_choices()
        self.fields.get("charge").initial = self.initial_charge()

    def clean_charge(self):
        charge = self.cleaned_data.get("charge")
        if charge and not charge.is_operational:
            self.add_error(
                "charge",
                "This charge is archived, and cannot be modified. Please contact an admin to get it restored.",
            )

        return charge

    def clean_date(self):
        date = self.cleaned_data.get("date")
        charge = self.cleaned_data.get("charge")
        if date.date() > timezone.now().date():
            raise ValidationError(
                "Payments cannot be scheduled for future dates.",
            )
        if charge and date.date() < charge.date.date():
            raise ValidationError(
                f"Payments cannot be paid before the charge date ({charge.date.date()}).",
            )
        source_date = self.instance.date if self.instance else timezone.now()
        if source_date:
            date = date.replace(
                hour=source_date.hour,
                minute=source_date.minute,
                second=source_date.second,
                microsecond=source_date.microsecond,
            )
        return date

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.pk and not self.instance.is_operational:
            self.add_error(None, "Changes to archived payment cannot be saved")
            return cleaned_data
        if not self.visit.is_operational:
            self.add_error(None, "Changes to archived visit cannot be saved")
            return cleaned_data
        amount = cleaned_data.get("amount")
        charge = cleaned_data.get("charge")
        if amount and charge and amount > charge.net_balance:
            self.add_error(
                "amount",
                f"Selected charge has an unpaid amount of {max(charge.net_balance, Decimal("0.00"))}",
            )

        return cleaned_data

    class Meta:
        model = Payment
        fields = ["charge", "amount", "payment_method", "date"]


class PatientPaymentForm(DynamicFormMixin, forms.ModelForm):
    def visit_choices(self):
        patient = self.patient or None
        print(patient)
        return (
            Visit.objects.exclude(is_active=False)
            .filter(patient=patient)
            .order_by("-date")
        )

    def initial_visit(self=None):
        if self and self.instance.pk:
            return self.instance.visit

        if hasattr(self, "patient") and self.patient:
            return (
                Visit.objects.exclude(is_active=False)
                .filter(patient=self.patient)
                .order_by("-date")
                .first()
            )
        return None

    def charge_choices(self):
        visit = self["visit"].value() or None
        return (
            Charge.objects.exclude(is_active=False)
            .filter(visit=visit)
            .order_by("-date")
        )

    def initial_charge(self):
        if self.instance.pk:
            return self.instance.charge

        visit = self["visit"].value() or None
        return (
            Charge.objects.exclude(is_active=False)
            .filter(visit=visit)
            .order_by("-date")
            .first()
        )

    visit = forms.ModelChoiceField(
        Visit.objects.exclude(is_active=False).order_by("-date"),
        required=True,
        initial=initial_visit,
        empty_label="Select a visit",
        widget=forms.Select(
            attrs={
                "class": "select select-bordered w-full",
            }
        ),
    )

    charge = DynamicField(
        forms.ModelChoiceField,
        queryset=charge_choices,
        initial=initial_charge,
        required=True,
        empty_label="Select a charge",
        widget=forms.Select(
            attrs={
                "class": "select select-bordered w-full",
            }
        ),
    )

    amount = forms.DecimalField(
        min_value=0.0,
        required=True,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Amount",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )

    payment_method = EnumChoiceField(
        enum=Payment.PaymentMethodEnum,
        choices=map(
            lambda choice: (choice.value, choice.label),
            Payment.selectable_payment_methods(),
        ),
        required=True,
        widget=forms.Select(
            attrs={
                "class": "select select-bordered w-full",
            }
        ),
    )

    date = forms.DateTimeField(
        initial=timezone.now().date,
        widget=forms.DateInput(
            attrs={"class": "input input-bordered w-full", "type": "date"}
        ),
    )

    def __init__(self, *args, patient=None, user=None, **kwargs):
        self.patient = patient
        self.user = user
        super().__init__(*args, **kwargs)

        if not hasattr(self, "cleaned_data"):
            self.cleaned_data = {}

        if self.instance.pk:
            msg = "Please use the update form for updates."
            self.add_error(None, msg)
            for field in self.fields.values():
                field.disabled = True
            self.disable_submit = True

        if patient and not patient.is_operational:
            msg = "This patient is archived, and cannot be modified. Please contact an admin to get them restored."
            self.add_error(None, msg)
            for field in self.fields.values():
                field.disabled = True
            self.disable_submit = True

        if self.user and self.user.role == Staff.RoleEnum.ADMIN:
            self.fields.get("payment_method").choices = (
                Payment.PaymentMethodEnum.choices
            )

        self.fields.get("visit").queryset = (
            Visit.objects.exclude(is_active=False)
            .filter(patient=self.patient)
            .order_by("-date")
        )

    def clean_visit(self):
        visit = self.cleaned_data.get("visit")
        if visit and not visit.is_operational:
            self.add_error(
                "visit",
                "This visit is archived, and cannot be modified. Please contact an admin to get it restored.",
            )

        return visit

    def clean_charge(self):
        charge = self.cleaned_data.get("charge")
        if charge and not charge.is_operational:
            self.add_error(
                "charge",
                "This charge is archived, and cannot be modified. Please contact an admin to get it restored.",
            )

        return charge

    def clean_date(self):
        date = self.cleaned_data.get("date")
        charge = self.cleaned_data.get("charge")
        if date.date() > timezone.now().date():
            raise ValidationError(
                "Payments cannot be scheduled for future dates.",
            )
        if charge and date.date() < charge.date.date():
            raise ValidationError(
                f"Payments cannot be paid before the charge date ({charge.date.date()}).",
            )
        source_date = self.instance.date if self.instance else timezone.now()
        if source_date:
            date = date.replace(
                hour=source_date.hour,
                minute=source_date.minute,
                second=source_date.second,
                microsecond=source_date.microsecond,
            )
        return date

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.pk and not self.instance.is_operational:
            self.add_error(None, "Changes to archived payment cannot be saved")
            return cleaned_data
        if not self.patient.is_operational:
            self.add_error(None, "Changes to archived patient cannot be saved")
            return cleaned_data
        amount = cleaned_data.get("amount")
        charge = cleaned_data.get("charge")
        if amount and charge and amount > charge.net_balance:
            self.add_error(
                "amount",
                f"Selected charge has an unpaid amount of {max(charge.net_balance, Decimal("0.00"))}",
            )

        return cleaned_data

    class Meta:
        model = Payment
        fields = ["amount", "payment_method", "date"]


class UpdatePaymentForm(forms.ModelForm):
    amount = forms.DecimalField(
        min_value=0.0,
        required=True,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Amount",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )

    payment_method = EnumChoiceField(
        enum=Payment.PaymentMethodEnum,
        choices=map(
            lambda choice: (choice.value, choice.label),
            Payment.selectable_payment_methods(),
        ),
        required=True,
        widget=forms.Select(
            attrs={
                "class": "select select-bordered w-full",
            }
        ),
    )

    date = forms.DateTimeField(
        initial=timezone.now().date,
        widget=forms.DateInput(
            attrs={"class": "input input-bordered w-full", "type": "date"}
        ),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        if not hasattr(self, "cleaned_data"):
            self.cleaned_data = {}

        if not self.instance.pk:
            for field in self.fields.values():
                field.disabled = True
            self.disable_submit = True
            self.add_error(
                None, "Please use the update form for existing payments only."
            )

        if not self.instance.is_operational:
            for field in self.fields.values():
                field.disabled = True
            self.disable_submit = True
            self.add_error(
                None,
                "This payment is archived, and cannot be modified. Please contact an admin to get it restored.",
            )

        if not (self.user and self.user.role == Staff.RoleEnum.ADMIN):
            self.fields.get("amount").widget.attrs["readonly"] = True
            self.fields.get("date").widget.attrs["readonly"] = True

    def clean_amount(self):
        if not (self.user and self.user.role == Staff.RoleEnum.ADMIN):
            return self.instance.amount
        return self.cleaned_data.get("amount")

    def clean_date(self):
        if not (self.user and self.user.role == Staff.RoleEnum.ADMIN):
            return self.instance.date

        date = self.cleaned_data.get("date")
        charge = self.instance.charge
        if not date or date.date() > timezone.now().date():
            raise ValidationError(
                "Payments cannot be scheduled for future dates.",
            )
        if charge and date.date() < charge.date.date():
            raise ValidationError(
                f"Payments cannot be paid before the charge date ({charge.date.date()}).",
            )
        return self.cleaned_data.get("date")

    class Meta:
        model = Payment
        fields = ["amount", "payment_method", "date"]


class AdjustmentForm(DynamicFormMixin, forms.ModelForm):
    def get_max_value(self):
        payment = self.payment
        if payment:
            return payment.net_paid
        return 0.0

    amount = DynamicField(
        forms.DecimalField,
        min_value=0.0,
        max_value=get_max_value,
        required=True,
        widget=forms.NumberInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Amount",
                "onwheel": "return false;",
                "onfocus": "this.addEventListener('wheel', function (e) { e.preventDefault() }, { passive: false })",
            }
        ),
    )

    reason = forms.CharField(
        required=True,
        widget=forms.TextInput(
            {
                "class": "input input-bordered w-full",
                "placeholder": "Reason for adjustment",
            }
        ),
    )

    date = forms.DateTimeField(
        initial=timezone.now().date,
        widget=forms.DateInput(
            attrs={"class": "input input-bordered w-full", "type": "date"}
        ),
    )

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")

        if not amount or amount > self.payment.net_paid:
            raise ValidationError(
                f"Amount must be between 0 and {round(self.payment.net_paid, 2)}"
            )
        return amount

    def __init__(self, *args, payment, **kwargs):
        self.payment = payment
        super().__init__(*args, **kwargs)

    class Meta:
        model = Adjustment
        fields = ["amount", "reason", "date"]
