from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q, Sum, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    AttendanceForm,
    DepartmentForm,
    EmployeeForm,
    LeaveRequestForm,
    PayrollForm,
    SalaryBandForm,
)
from .models import Attendance, Department, Employee, LeaveRequest, Payroll, SalaryBand


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, f"Welcome back, {user.get_username()}!")
            next_url = request.POST.get("next") or request.GET.get("next")
            return redirect(next_url or "dashboard")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, "payroll/login.html", {"form": form})


@login_required
def logout_view(request):
    auth_logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")


@login_required
def profile_view(request):
    employee = getattr(request.user, "employee_profile", None)
    return render(request, "payroll/profile.html", {"employee": employee})


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required
def dashboard_view(request):
    total_employees = Employee.objects.count()
    active_employees = Employee.objects.filter(is_active=True).count()
    total_departments = Department.objects.count()
    pending_leaves = LeaveRequest.objects.filter(status=LeaveRequest.PENDING).count()
    total_payroll_records = Payroll.objects.count()
    total_payroll_amount = Payroll.objects.aggregate(total=Sum("net_salary"))["total"] or 0

    recent_employees = Employee.objects.select_related("department", "salary_band").order_by("-id")[:5]
    recent_attendance = Attendance.objects.select_related("employee").order_by("-date", "-id")[:5]
    recent_leaves = LeaveRequest.objects.select_related("employee").order_by("-id")[:5]
    recent_payroll = Payroll.objects.select_related("employee").order_by("-id")[:5]

    department_stats = Department.objects.annotate(emp_count=Count("employees")).order_by("-emp_count")

    context = {
        "total_employees": total_employees,
        "active_employees": active_employees,
        "total_departments": total_departments,
        "pending_leaves": pending_leaves,
        "total_payroll_records": total_payroll_records,
        "total_payroll_amount": total_payroll_amount,
        "recent_employees": recent_employees,
        "recent_attendance": recent_attendance,
        "recent_leaves": recent_leaves,
        "recent_payroll": recent_payroll,
        "department_stats": department_stats,
    }
    return render(request, "payroll/dashboard.html", context)


# ---------------------------------------------------------------------------
# Employees
# ---------------------------------------------------------------------------

@login_required
def employee_list(request):
    employees = Employee.objects.select_related("department", "salary_band").all()

    query = request.GET.get("q", "").strip()
    if query:
        employees = employees.filter(
            Q(employee_id__icontains=query)
            | Q(full_name__icontains=query)
            | Q(email__icontains=query)
        )

    department_id = request.GET.get("department", "")
    if department_id:
        employees = employees.filter(department_id=department_id)

    status = request.GET.get("status", "")
    if status == "active":
        employees = employees.filter(is_active=True)
    elif status == "inactive":
        employees = employees.filter(is_active=False)

    context = {
        "employees": employees,
        "departments": Department.objects.all(),
        "query": query,
        "selected_department": department_id,
        "selected_status": status,
    }
    return render(request, "payroll/employees.html", context)


@login_required
def employee_add(request):
    if request.method == "POST":
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Employee created successfully.")
            return redirect("employee_list")
    else:
        form = EmployeeForm()
    return render(request, "payroll/employee_form.html", {"form": form, "title": "Add Employee"})


@login_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == "POST":
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, "Employee updated successfully.")
            return redirect("employee_list")
    else:
        form = EmployeeForm(instance=employee)
    return render(request, "payroll/employee_form.html", {"form": form, "title": "Edit Employee", "employee": employee})


@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee.objects.select_related("department", "salary_band", "manager"), pk=pk)
    context = {
        "employee": employee,
        "attendance_records": employee.attendance_records.all()[:20],
        "leave_requests": employee.leave_requests.all(),
        "payroll_records": employee.payroll_records.all(),
    }
    return render(request, "payroll/employee_detail.html", context)


@login_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == "POST":
        name = employee.full_name
        employee.delete()
        messages.success(request, f"Employee '{name}' deleted successfully.")
        return redirect("employee_list")
    return render(request, "payroll/employee_detail.html", {"employee": employee, "confirm_delete": True})


@login_required
def employee_toggle_active(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == "POST":
        employee.is_active = not employee.is_active
        employee.save()
        state = "activated" if employee.is_active else "deactivated"
        messages.success(request, f"Employee '{employee.full_name}' {state} successfully.")
    return redirect("employee_list")


# ---------------------------------------------------------------------------
# Departments
# ---------------------------------------------------------------------------

@login_required
def department_list(request):
    departments = Department.objects.annotate(emp_count=Count("employees"))
    return render(request, "payroll/departments.html", {"departments": departments})


@login_required
def department_add(request):
    if request.method == "POST":
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Department created successfully.")
            return redirect("department_list")
    else:
        form = DepartmentForm()
    return render(request, "payroll/department_form.html", {"form": form, "title": "Add Department"})


@login_required
def department_edit(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == "POST":
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, "Department updated successfully.")
            return redirect("department_list")
    else:
        form = DepartmentForm(instance=department)
    return render(request, "payroll/department_form.html", {"form": form, "title": "Edit Department"})


@login_required
def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == "POST":
        if department.employees.exists():
            messages.error(
                request,
                f"Cannot delete '{department.name}' because it still has employees assigned to it.",
            )
        else:
            name = department.name
            department.delete()
            messages.success(request, f"Department '{name}' deleted successfully.")
        return redirect("department_list")
    return redirect("department_list")


# ---------------------------------------------------------------------------
# Salary Bands
# ---------------------------------------------------------------------------

@login_required
def salary_band_list(request):
    salary_bands = SalaryBand.objects.annotate(emp_count=Count("employees"))
    return render(request, "payroll/salary_bands.html", {"salary_bands": salary_bands})


@login_required
def salary_band_add(request):
    if request.method == "POST":
        form = SalaryBandForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Salary band created successfully.")
            return redirect("salary_band_list")
    else:
        form = SalaryBandForm()
    return render(request, "payroll/salary_band_form.html", {"form": form, "title": "Add Salary Band"})


@login_required
def salary_band_edit(request, pk):
    salary_band = get_object_or_404(SalaryBand, pk=pk)
    if request.method == "POST":
        form = SalaryBandForm(request.POST, instance=salary_band)
        if form.is_valid():
            form.save()
            messages.success(request, "Salary band updated successfully.")
            return redirect("salary_band_list")
    else:
        form = SalaryBandForm(instance=salary_band)
    return render(request, "payroll/salary_band_form.html", {"form": form, "title": "Edit Salary Band"})


@login_required
def salary_band_delete(request, pk):
    salary_band = get_object_or_404(SalaryBand, pk=pk)
    if request.method == "POST":
        if salary_band.employees.exists():
            messages.error(
                request,
                f"Cannot delete '{salary_band.name}' because it still has employees assigned to it.",
            )
        else:
            name = salary_band.name
            salary_band.delete()
            messages.success(request, f"Salary band '{name}' deleted successfully.")
        return redirect("salary_band_list")
    return redirect("salary_band_list")


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------

@login_required
def attendance_list(request):
    records = Attendance.objects.select_related("employee").all()

    employee_id = request.GET.get("employee", "")
    if employee_id:
        records = records.filter(employee_id=employee_id)

    status = request.GET.get("status", "")
    if status:
        records = records.filter(status=status)

    date = request.GET.get("date", "")
    if date:
        records = records.filter(date=date)

    context = {
        "records": records,
        "employees": Employee.objects.all(),
        "status_choices": Attendance.STATUS_CHOICES,
        "selected_employee": employee_id,
        "selected_status": status,
        "selected_date": date,
    }
    return render(request, "payroll/attendance.html", context)


@login_required
def attendance_add(request):
    if request.method == "POST":
        form = AttendanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Attendance record created successfully.")
            return redirect("attendance_list")
    else:
        form = AttendanceForm(initial={"date": timezone.now().date()})
    return render(request, "payroll/attendance_form.html", {"form": form, "title": "Add Attendance"})


@login_required
def attendance_edit(request, pk):
    record = get_object_or_404(Attendance, pk=pk)
    if request.method == "POST":
        form = AttendanceForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, "Attendance record updated successfully.")
            return redirect("attendance_list")
    else:
        form = AttendanceForm(instance=record)
    return render(request, "payroll/attendance_form.html", {"form": form, "title": "Edit Attendance"})


@login_required
def attendance_delete(request, pk):
    record = get_object_or_404(Attendance, pk=pk)
    if request.method == "POST":
        record.delete()
        messages.success(request, "Attendance record deleted successfully.")
        return redirect("attendance_list")
    return redirect("attendance_list")


# ---------------------------------------------------------------------------
# Leave Requests
# ---------------------------------------------------------------------------

@login_required
def leave_list(request):
    leaves = LeaveRequest.objects.select_related("employee").all()

    status = request.GET.get("status", "")
    if status:
        leaves = leaves.filter(status=status)

    employee_id = request.GET.get("employee", "")
    if employee_id:
        leaves = leaves.filter(employee_id=employee_id)

    context = {
        "leaves": leaves,
        "employees": Employee.objects.all(),
        "status_choices": LeaveRequest.STATUS_CHOICES,
        "selected_status": status,
        "selected_employee": employee_id,
    }
    return render(request, "payroll/leave_requests.html", context)


@login_required
def leave_add(request):
    if request.method == "POST":
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Leave request created successfully.")
            return redirect("leave_list")
    else:
        form = LeaveRequestForm()
    return render(request, "payroll/leave_form.html", {"form": form, "title": "New Leave Request"})


@login_required
def leave_edit(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    if request.method == "POST":
        form = LeaveRequestForm(request.POST, instance=leave)
        if form.is_valid():
            form.save()
            messages.success(request, "Leave request updated successfully.")
            return redirect("leave_list")
    else:
        form = LeaveRequestForm(instance=leave)
    return render(request, "payroll/leave_form.html", {"form": form, "title": "Edit Leave Request"})


@login_required
def leave_delete(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    if request.method == "POST":
        leave.delete()
        messages.success(request, "Leave request deleted successfully.")
        return redirect("leave_list")
    return redirect("leave_list")


@login_required
def leave_approve(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    if request.method == "POST":
        leave.status = LeaveRequest.APPROVED
        leave.save()
        messages.success(request, f"Leave request for {leave.employee.full_name} approved.")
    return redirect("leave_list")


@login_required
def leave_reject(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    if request.method == "POST":
        leave.status = LeaveRequest.REJECTED
        leave.save()
        messages.success(request, f"Leave request for {leave.employee.full_name} rejected.")
    return redirect("leave_list")


# ---------------------------------------------------------------------------
# Payroll
# ---------------------------------------------------------------------------

@login_required
def payroll_list(request):
    records = Payroll.objects.select_related("employee").all()

    employee_id = request.GET.get("employee", "")
    if employee_id:
        records = records.filter(employee_id=employee_id)

    month = request.GET.get("month", "")
    if month:
        records = records.filter(month=month)

    year = request.GET.get("year", "")
    if year:
        records = records.filter(year=year)

    summary = records.aggregate(
        total_basic=Sum("basic_salary"),
        total_allowances=Sum("allowances"),
        total_deductions=Sum("deductions"),
        total_net=Sum("net_salary"),
    )

    years = Payroll.objects.order_by("-year").values_list("year", flat=True).distinct()

    context = {
        "records": records,
        "employees": Employee.objects.all(),
        "month_choices": Payroll.MONTH_CHOICES,
        "years": years,
        "summary": summary,
        "selected_employee": employee_id,
        "selected_month": month,
        "selected_year": year,
    }
    return render(request, "payroll/payroll.html", context)


@login_required
def payroll_add(request):
    if request.method == "POST":
        form = PayrollForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Payroll record created successfully.")
            return redirect("payroll_list")
    else:
        form = PayrollForm()
    return render(request, "payroll/payroll_form.html", {"form": form, "title": "Add Payroll Record"})


@login_required
def payroll_edit(request, pk):
    record = get_object_or_404(Payroll, pk=pk)
    if request.method == "POST":
        form = PayrollForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, "Payroll record updated successfully.")
            return redirect("payroll_list")
    else:
        form = PayrollForm(instance=record)
    return render(request, "payroll/payroll_form.html", {"form": form, "title": "Edit Payroll Record"})


@login_required
def payroll_detail(request, pk):
    record = get_object_or_404(Payroll.objects.select_related("employee"), pk=pk)
    return render(request, "payroll/payroll_form.html", {"record": record, "view_only": True, "title": "Payroll Details"})


@login_required
def payroll_delete(request, pk):
    record = get_object_or_404(Payroll, pk=pk)
    if request.method == "POST":
        record.delete()
        messages.success(request, "Payroll record deleted successfully.")
        return redirect("payroll_list")
    return redirect("payroll_list")
