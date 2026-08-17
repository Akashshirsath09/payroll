from django.contrib import admin

from .models import Attendance, Department, Employee, LeaveRequest, Payroll, SalaryBand


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "employee_count")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(SalaryBand)
class SalaryBandAdmin(admin.ModelAdmin):
    list_display = ("name", "min_salary", "max_salary", "employee_count")
    search_fields = ("name",)
    ordering = ("min_salary",)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "full_name", "email", "department", "salary_band", "joining_date", "is_active")
    list_filter = ("department", "salary_band", "is_active")
    search_fields = ("employee_id", "full_name", "email")
    ordering = ("full_name",)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "date", "status")
    list_filter = ("status", "date")
    search_fields = ("employee__full_name", "employee__employee_id")
    ordering = ("-date",)


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ("employee", "start_date", "end_date", "status")
    list_filter = ("status",)
    search_fields = ("employee__full_name", "employee__employee_id")
    ordering = ("-start_date",)


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ("employee", "month", "year", "basic_salary", "allowances", "deductions", "net_salary", "paid_on")
    list_filter = ("month", "year")
    search_fields = ("employee__full_name", "employee__employee_id")
    ordering = ("-year", "-month")
