from django.db import models
from django.contrib.auth.models import User

class GeneralTimetable(models.Model):
    academic_year = models.CharField(max_length=20)
    config = models.JSONField()
    timetable = models.JSONField()
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.academic_year} timetable ({self.created_at:%Y-%m-%d})'

class ConflictRecord(models.Model):
    conflict_date = models.DateField(db_index=True)
    class_name = models.CharField(max_length=80)
    section = models.CharField(max_length=30)
    day = models.CharField(max_length=20)
    period_no = models.PositiveIntegerField()
    absent_teacher = models.CharField(max_length=120)
    replacement_teacher = models.CharField(max_length=120)
    original_subject = models.CharField(max_length=120)
    replacement_subject = models.CharField(max_length=120)
    timetable_snapshot = models.JSONField()
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f'{self.conflict_date} — {self.class_name} {self.section}'
