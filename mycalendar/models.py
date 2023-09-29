from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=40, blank=False)
    department_code = models.CharField(max_length=12, blank=False)
    def __str__(self):
        return f'{self.name},{self.id}' 

# Create your models here.
class LeaveRequest(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    name = models.CharField(max_length=255)
    leave_bal = models.IntegerField(null=True, default='0')
    department_id = models.ForeignKey(Department, on_delete = models.PROTECT, null = True, blank = True, related_name = 'Department')
    leave_ent = models.IntegerField(null=False, unique=True)

    def __str__(self):
        return f'{self.name}, {self.start_date} to {self.end_date}' 
