import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from payroll.models import Attendance, Department, Employee, LeaveRequest, Payroll, SalaryBand


class Command(BaseCommand):
    help = "Seed the database with sample payroll data (safe to re-run)."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding sample data...")

        # Superuser / admin login
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "admin123")
            self.stdout.write(self.style.SUCCESS("Created superuser 'admin' / 'admin123'"))

        department_names = [
            ("Human Resources", "Handles recruitment, onboarding and employee relations."),
            ("Finance", "Manages budgets, accounting and financial reporting."),
            ("IT", "Maintains technology infrastructure and software systems."),
            ("Sales", "Drives revenue through client acquisition and account growth."),
            ("Marketing", "Builds brand awareness and manages campaigns."),
        ]
        departments = {}
        for name, desc in department_names:
            dept, _ = Department.objects.get_or_create(name=name, defaults={"description": desc})
            departments[name] = dept

        band_data = [
            ("Junior", 25000, 40000),
            ("Mid Level", 40000, 65000),
            ("Senior", 65000, 95000),
            ("Manager", 95000, 130000),
            ("Executive", 130000, 200000),
        ]
        bands = {}
        for name, mn, mx in band_data:
            band, _ = SalaryBand.objects.get_or_create(
                name=name, defaults={"min_salary": Decimal(mn), "max_salary": Decimal(mx)}
            )
            bands[name] = band

        first_names = ["Aarav", "Priya", "Rohan", "Sneha", "Vikram", "Anita", "Karan", "Neha",
                        "Arjun", "Divya", "Rahul", "Pooja", "Sanjay", "Meera", "Amit", "Kavya"]
        last_names = ["Sharma", "Verma", "Patel", "Gupta", "Reddy", "Nair", "Iyer", "Singh",
                      "Kumar", "Rao", "Mehta", "Joshi"]

        dept_names_list = list(departments.keys())
        band_names_list = list(bands.keys())

        employees = list(Employee.objects.all())
        if not employees:
            managers = []
            for i in range(1, 26):
                fname = random.choice(first_names)
                lname = random.choice(last_names)
                full_name = f"{fname} {lname}"
                emp_id = f"EMP{i:04d}"
                email = f"{fname.lower()}.{lname.lower()}{i}@company.com"
                dept = departments[random.choice(dept_names_list)]
                band = bands[random.choice(band_names_list)]
                manager = random.choice(managers) if managers and random.random() > 0.3 else None
                joining_date = date.today() - timedelta(days=random.randint(60, 1500))

                employee = Employee.objects.create(
                    employee_id=emp_id,
                    full_name=full_name,
                    email=email,
                    department=dept,
                    salary_band=band,
                    manager=manager,
                    joining_date=joining_date,
                    is_active=random.random() > 0.15,
                )
                employees.append(employee)
                if random.random() > 0.6:
                    managers.append(employee)

            self.stdout.write(self.style.SUCCESS(f"Created {len(employees)} employees."))

        # Attendance for last 14 days
        today = date.today()
        attendance_created = 0
        for employee in employees:
            for day_offset in range(14):
                day = today - timedelta(days=day_offset)
                if day.weekday() >= 5:
                    continue
                if Attendance.objects.filter(employee=employee, date=day).exists():
                    continue
                status = random.choices(
                    [Attendance.PRESENT, Attendance.ABSENT, Attendance.HALF_DAY],
                    weights=[85, 8, 7],
                )[0]
                Attendance.objects.create(employee=employee, date=day, status=status)
                attendance_created += 1
        self.stdout.write(self.style.SUCCESS(f"Created {attendance_created} attendance records."))

        # Leave requests
        leave_reasons = [
            "Family function", "Medical appointment", "Personal reasons",
            "Vacation", "Not feeling well", "Relocation", "Wedding in family",
        ]
        leaves_created = 0
        if LeaveRequest.objects.count() < 15:
            for _ in range(15):
                employee = random.choice(employees)
                start = today + timedelta(days=random.randint(-30, 30))
                end = start + timedelta(days=random.randint(0, 5))
                status = random.choice([LeaveRequest.PENDING, LeaveRequest.APPROVED, LeaveRequest.REJECTED])
                LeaveRequest.objects.create(
                    employee=employee,
                    start_date=start,
                    end_date=end,
                    reason=random.choice(leave_reasons),
                    status=status,
                )
                leaves_created += 1
        self.stdout.write(self.style.SUCCESS(f"Created {leaves_created} leave requests."))

        # Payroll records for last 3 months
        payroll_created = 0
        month_year_pairs = []
        y, m = today.year, today.month
        for _ in range(3):
            month_year_pairs.append((m, y))
            m -= 1
            if m == 0:
                m = 12
                y -= 1

        for employee in employees:
            band = employee.salary_band
            basic = Decimal(random.randint(int(band.min_salary), int(band.max_salary)))
            for month, year in month_year_pairs:
                if Payroll.objects.filter(employee=employee, month=month, year=year).exists():
                    continue
                allowances = (basic * Decimal("0.10")).quantize(Decimal("0.01"))
                deductions = (basic * Decimal("0.05")).quantize(Decimal("0.01"))
                Payroll.objects.create(
                    employee=employee,
                    month=month,
                    year=year,
                    basic_salary=basic,
                    allowances=allowances,
                    deductions=deductions,
                    paid_on=date(year, month, min(28, 28)),
                )
                payroll_created += 1
        self.stdout.write(self.style.SUCCESS(f"Created {payroll_created} payroll records."))

        self.stdout.write(self.style.SUCCESS("Sample data seeding complete."))
