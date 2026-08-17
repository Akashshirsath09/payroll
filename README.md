# Payroll Management System (Django)

A complete, working Django payroll management system with authentication,
employee/department/salary-band management, attendance, leave requests, and
payroll processing with automatic net-salary calculation.

## Tech stack
Python 3, Django, SQLite3, Django Templates, vanilla CSS/JS.

## Setup

```bash
cd payroll_project
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install django

python manage.py makemigrations
python manage.py migrate

# Optional: create sample departments, salary bands, employees,
# attendance, leave requests, payroll records, and an admin login.
python manage.py seed_data

python manage.py runserver
```

Visit **http://127.0.0.1:8000/**.

## Demo login (created by `seed_data`)
- Username: `admin`
- Password: `admin123`

This account is also a Django superuser, so it can access `/admin/` too.

If you skip `seed_data`, create your own login with:

```bash
python manage.py createsuperuser
```

## Running tests

```bash
python manage.py test
```

18 tests cover model validation (payroll net-salary calculation, salary-band
and leave-date validation, duplicate attendance prevention), authentication
protection, and full CRUD flows for employees and payroll.

## Project layout

```
payroll_project/
├── manage.py
├── config/            # project settings, urls, wsgi/asgi
└── payroll/           # the app: models, views, forms, admin, urls
    ├── templates/payroll/
    ├── static/payroll/{css,js}
    ├── management/commands/seed_data.py
    └── migrations/
```

## Notes
- All money fields use `Decimal`, never floats.
- `Payroll.net_salary` is recomputed and validated on every save
  (`basic_salary + allowances - deductions`), so it can never drift out of sync.
- Departments and salary bands can't be deleted while employees still
  reference them (a friendly message explains why, instead of an error page).
- Attendance enforces one record per employee per day at the database level.
- Payroll enforces one record per employee per month/year at the database level.
