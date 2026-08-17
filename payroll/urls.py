from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),

    # Employees
    path("employees/", views.employee_list, name="employee_list"),
    path("employees/add/", views.employee_add, name="employee_add"),
    path("employees/<int:pk>/", views.employee_detail, name="employee_detail"),
    path("employees/<int:pk>/edit/", views.employee_edit, name="employee_edit"),
    path("employees/<int:pk>/delete/", views.employee_delete, name="employee_delete"),
    path("employees/<int:pk>/toggle-active/", views.employee_toggle_active, name="employee_toggle_active"),

    # Departments
    path("departments/", views.department_list, name="department_list"),
    path("departments/add/", views.department_add, name="department_add"),
    path("departments/<int:pk>/edit/", views.department_edit, name="department_edit"),
    path("departments/<int:pk>/delete/", views.department_delete, name="department_delete"),

    # Salary Bands
    path("salary-bands/", views.salary_band_list, name="salary_band_list"),
    path("salary-bands/add/", views.salary_band_add, name="salary_band_add"),
    path("salary-bands/<int:pk>/edit/", views.salary_band_edit, name="salary_band_edit"),
    path("salary-bands/<int:pk>/delete/", views.salary_band_delete, name="salary_band_delete"),

    # Attendance
    path("attendance/", views.attendance_list, name="attendance_list"),
    path("attendance/add/", views.attendance_add, name="attendance_add"),
    path("attendance/<int:pk>/edit/", views.attendance_edit, name="attendance_edit"),
    path("attendance/<int:pk>/delete/", views.attendance_delete, name="attendance_delete"),

    # Leave Requests
    path("leaves/", views.leave_list, name="leave_list"),
    path("leaves/add/", views.leave_add, name="leave_add"),
    path("leaves/<int:pk>/edit/", views.leave_edit, name="leave_edit"),
    path("leaves/<int:pk>/delete/", views.leave_delete, name="leave_delete"),
    path("leaves/<int:pk>/approve/", views.leave_approve, name="leave_approve"),
    path("leaves/<int:pk>/reject/", views.leave_reject, name="leave_reject"),

    # Payroll
    path("payroll/", views.payroll_list, name="payroll_list"),
    path("payroll/add/", views.payroll_add, name="payroll_add"),
    path("payroll/<int:pk>/", views.payroll_detail, name="payroll_detail"),
    path("payroll/<int:pk>/edit/", views.payroll_edit, name="payroll_edit"),
    path("payroll/<int:pk>/delete/", views.payroll_delete, name="payroll_delete"),
]
