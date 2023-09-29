from django.contrib import admin
from .models import LeaveRequest, Department

# Register your models here.
admin.site.register(LeaveRequest)
admin.site.register(Department)