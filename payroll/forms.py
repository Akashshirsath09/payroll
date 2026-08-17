from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Attendance, Department, Employee, LeaveRequest, Payroll, SalaryBand

WIDGET_CLASS = "form-control"


class StyledFormMixin:
    """Adds a consistent CSS class to all visible fields."""

    def style_fields(self):
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            if isinstance(field.widget, (forms.CheckboxInput,)):
                field.widget.attrs["class"] = (existing + " form-check-input").strip()
            else:
                field.widget.attrs["class"] = (existing + " " + WIDGET_CLASS).strip()


class LoginForm(StyledFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()


class DepartmentForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()


class SalaryBandForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = SalaryBand
        fields = ["name", "min_salary", "max_salary"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()

    def clean(self):
        cleaned_data = super().clean()
        min_salary = cleaned_data.get("min_salary")
        max_salary = cleaned_data.get("max_salary")
        if min_salary is not None and max_salary is not None and min_salary > max_salary:
            raise forms.ValidationError("Minimum salary cannot be greater than maximum salary.")
        return cleaned_data


class EmployeeForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            "employee_id", "full_name", "email", "department",
            "salary_band", "manager", "joining_date", "is_active",
        ]
        widgets = {
            "joining_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()
        instance = kwargs.get("instance")
        qs = Employee.objects.all()
        if instance and instance.pk:
            qs = qs.exclude(pk=instance.pk)
        self.fields["manager"].queryset = qs

    def clean_email(self):
        email = self.cleaned_data["email"]
        qs = Employee.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("An employee with this email already exists.")
        return email

    def clean_employee_id(self):
        employee_id = self.cleaned_data["employee_id"]
        qs = Employee.objects.filter(employee_id__iexact=employee_id)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("An employee with this ID already exists.")
        return employee_id

    def clean(self):
        cleaned_data = super().clean()
        manager = cleaned_data.get("manager")
        if manager and self.instance and manager.pk == self.instance.pk:
            raise forms.ValidationError("An employee cannot be their own manager.")
        return cleaned_data


class AttendanceForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ["employee", "date", "status"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()

    def clean(self):
        cleaned_data = super().clean()
        employee = cleaned_data.get("employee")
        date = cleaned_data.get("date")
        if employee and date:
            qs = Attendance.objects.filter(employee=employee, date=date)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    "An attendance record for this employee on this date already exists."
                )
        return cleaned_data


class LeaveRequestForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ["employee", "start_date", "end_date", "reason", "status"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "reason": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError("End date cannot be before start date.")
        return cleaned_data


class PayrollForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Payroll
        fields = ["employee", "month", "year", "basic_salary", "allowances", "deductions", "paid_on"]
        widgets = {
            "paid_on": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()

    def clean_basic_salary(self):
        value = self.cleaned_data["basic_salary"]
        if value < 0:
            raise forms.ValidationError("Basic salary cannot be negative.")
        return value

    def clean_allowances(self):
        value = self.cleaned_data["allowances"]
        if value < 0:
            raise forms.ValidationError("Allowances cannot be negative.")
        return value

    def clean_deductions(self):
        value = self.cleaned_data["deductions"]
        if value < 0:
            raise forms.ValidationError("Deductions cannot be negative.")
        return value

    def clean(self):
        cleaned_data = super().clean()
        employee = cleaned_data.get("employee")
        month = cleaned_data.get("month")
        year = cleaned_data.get("year")
        if employee and month and year:
            qs = Payroll.objects.filter(employee=employee, month=month, year=year)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(
                    "A payroll record for this employee, month and year already exists."
                )
        return cleaned_data
