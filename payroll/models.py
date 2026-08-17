from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def employee_count(self):
        return self.employees.count()


class SalaryBand(models.Model):
    name = models.CharField(max_length=50)
    min_salary = models.DecimalField(max_digits=12, decimal_places=2)
    max_salary = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["min_salary"]

    def __str__(self):
        return f"{self.name} ({self.min_salary} - {self.max_salary})"

    @property
    def employee_count(self):
        return self.employees.count()

    def clean(self):
        if self.min_salary is not None and self.max_salary is not None:
            if self.min_salary > self.max_salary:
                raise ValidationError("Minimum salary cannot be greater than maximum salary.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Employee(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="employee_profile"
    )
    employee_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name="employees"
    )
    salary_band = models.ForeignKey(
        SalaryBand, on_delete=models.PROTECT, related_name="employees"
    )
    manager = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="direct_reports"
    )
    joining_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.employee_id} - {self.full_name}"


class Attendance(models.Model):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    HALF_DAY = "HALF_DAY"

    STATUS_CHOICES = [
        (PRESENT, "Present"),
        (ABSENT, "Absent"),
        (HALF_DAY, "Half Day"),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PRESENT)

    class Meta:
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(fields=["employee", "date"], name="unique_attendance_per_day")
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} - {self.get_status_display()}"


class LeaveRequest(models.Model):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (APPROVED, "Approved"),
        (REJECTED, "Rejected"),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="leave_requests")
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.employee.full_name} - {self.start_date} to {self.end_date}"

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date.")


class Payroll(models.Model):
    MONTH_CHOICES = [
        (1, "January"), (2, "February"), (3, "March"), (4, "April"),
        (5, "May"), (6, "June"), (7, "July"), (8, "August"),
        (9, "September"), (10, "October"), (11, "November"), (12, "December"),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="payroll_records")
    month = models.IntegerField(choices=MONTH_CHOICES)
    year = models.IntegerField()
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    allowances = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    deductions = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    net_salary = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    paid_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-year", "-month"]
        constraints = [
            models.UniqueConstraint(fields=["employee", "month", "year"], name="unique_payroll_per_month")
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_month_display()} {self.year}"

    def clean(self):
        if self.basic_salary is not None and self.basic_salary < 0:
            raise ValidationError("Basic salary cannot be negative.")
        if self.allowances is not None and self.allowances < 0:
            raise ValidationError("Allowances cannot be negative.")
        if self.deductions is not None and self.deductions < 0:
            raise ValidationError("Deductions cannot be negative.")

    def save(self, *args, **kwargs):
        basic = self.basic_salary or Decimal("0.00")
        allowances = self.allowances or Decimal("0.00")
        deductions = self.deductions or Decimal("0.00")
        self.net_salary = basic + allowances - deductions
        self.full_clean()
        super().save(*args, **kwargs)
