from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Attendance, Department, Employee, LeaveRequest, Payroll, SalaryBand


class BaseSetupMixin:
    def create_base_data(self):
        self.department = Department.objects.create(name="Engineering", description="Builds the product.")
        self.salary_band = SalaryBand.objects.create(
            name="Mid Level", min_salary=Decimal("40000"), max_salary=Decimal("65000")
        )
        self.employee = Employee.objects.create(
            employee_id="EMP0001",
            full_name="Test Employee",
            email="test.employee@example.com",
            department=self.department,
            salary_band=self.salary_band,
            joining_date=date.today() - timedelta(days=100),
            is_active=True,
        )


class ModelTests(BaseSetupMixin, TestCase):
    def setUp(self):
        self.create_base_data()

    def test_department_creation(self):
        self.assertEqual(Department.objects.count(), 1)
        self.assertEqual(str(self.department), "Engineering")

    def test_employee_creation(self):
        self.assertEqual(Employee.objects.count(), 1)
        self.assertEqual(self.employee.department, self.department)

    def test_salary_band_validation(self):
        with self.assertRaises(Exception):
            SalaryBand.objects.create(name="Bad Band", min_salary=Decimal("100"), max_salary=Decimal("50"))

    def test_attendance_creation(self):
        record = Attendance.objects.create(employee=self.employee, date=date.today(), status=Attendance.PRESENT)
        self.assertEqual(record.status, Attendance.PRESENT)

    def test_attendance_duplicate_rejected(self):
        Attendance.objects.create(employee=self.employee, date=date.today(), status=Attendance.PRESENT)
        with self.assertRaises(Exception):
            Attendance.objects.create(employee=self.employee, date=date.today(), status=Attendance.ABSENT)

    def test_leave_validation(self):
        leave = LeaveRequest(
            employee=self.employee,
            start_date=date.today(),
            end_date=date.today() - timedelta(days=1),
            reason="Invalid range",
        )
        with self.assertRaises(Exception):
            leave.full_clean()

    def test_payroll_calculation(self):
        payroll = Payroll.objects.create(
            employee=self.employee,
            month=1,
            year=2026,
            basic_salary=Decimal("50000.00"),
            allowances=Decimal("5000.00"),
            deductions=Decimal("2000.00"),
        )
        self.assertEqual(payroll.net_salary, Decimal("53000.00"))


class ViewAccessTests(BaseSetupMixin, TestCase):
    def setUp(self):
        self.create_base_data()
        self.user = User.objects.create_user(username="tester", password="testpass123")

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_dashboard_access_when_logged_in(self):
        self.client.login(username="tester", password="testpass123")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dashboard", response.content)

    def test_login_view(self):
        response = self.client.post(reverse("login"), {"username": "tester", "password": "testpass123"})
        self.assertEqual(response.status_code, 302)


class EmployeeCRUDTests(BaseSetupMixin, TestCase):
    def setUp(self):
        self.create_base_data()
        self.user = User.objects.create_user(username="tester", password="testpass123")
        self.client.login(username="tester", password="testpass123")

    def test_employee_list_view(self):
        response = self.client.get(reverse("employee_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Employee")

    def test_employee_create_view(self):
        response = self.client.post(reverse("employee_add"), {
            "employee_id": "EMP0002",
            "full_name": "New Employee",
            "email": "new.employee@example.com",
            "department": self.department.pk,
            "salary_band": self.salary_band.pk,
            "joining_date": date.today(),
            "is_active": "on",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Employee.objects.filter(employee_id="EMP0002").exists())

    def test_employee_duplicate_email_rejected(self):
        response = self.client.post(reverse("employee_add"), {
            "employee_id": "EMP0003",
            "full_name": "Duplicate Employee",
            "email": self.employee.email,
            "department": self.department.pk,
            "salary_band": self.salary_band.pk,
            "joining_date": date.today(),
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Employee.objects.filter(employee_id="EMP0003").exists())

    def test_employee_update_view(self):
        response = self.client.post(reverse("employee_edit", args=[self.employee.pk]), {
            "employee_id": self.employee.employee_id,
            "full_name": "Updated Name",
            "email": self.employee.email,
            "department": self.department.pk,
            "salary_band": self.salary_band.pk,
            "joining_date": self.employee.joining_date,
            "is_active": "on",
        })
        self.assertEqual(response.status_code, 302)
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.full_name, "Updated Name")

    def test_employee_delete_view(self):
        response = self.client.post(reverse("employee_delete", args=[self.employee.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Employee.objects.filter(pk=self.employee.pk).exists())


class PayrollCRUDTests(BaseSetupMixin, TestCase):
    def setUp(self):
        self.create_base_data()
        self.user = User.objects.create_user(username="tester", password="testpass123")
        self.client.login(username="tester", password="testpass123")

    def test_payroll_create_view(self):
        response = self.client.post(reverse("payroll_add"), {
            "employee": self.employee.pk,
            "month": 3,
            "year": 2026,
            "basic_salary": "40000.00",
            "allowances": "2000.00",
            "deductions": "1000.00",
        })
        self.assertEqual(response.status_code, 302)
        record = Payroll.objects.get(employee=self.employee, month=3, year=2026)
        self.assertEqual(record.net_salary, Decimal("41000.00"))

    def test_payroll_list_view(self):
        Payroll.objects.create(
            employee=self.employee, month=1, year=2026,
            basic_salary=Decimal("40000"), allowances=Decimal("1000"), deductions=Decimal("500"),
        )
        response = self.client.get(reverse("payroll_list"))
        self.assertEqual(response.status_code, 200)

    def test_payroll_delete_view(self):
        record = Payroll.objects.create(
            employee=self.employee, month=2, year=2026,
            basic_salary=Decimal("40000"), allowances=Decimal("1000"), deductions=Decimal("500"),
        )
        response = self.client.post(reverse("payroll_delete", args=[record.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Payroll.objects.filter(pk=record.pk).exists())
