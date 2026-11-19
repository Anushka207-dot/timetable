from django import forms
class GeneralTimetableForm(forms.Form):
    academic_year=forms.CharField(max_length=20)
    days=forms.CharField(help_text='Comma-separated, e.g. Monday,Tuesday,Wednesday,Thursday,Friday')
    periods=forms.IntegerField(min_value=1,max_value=12)
    start_time=forms.TimeField()
    period_minutes=forms.IntegerField(min_value=20,max_value=120)
    break_after=forms.IntegerField(min_value=0,max_value=12)
    break_minutes=forms.IntegerField(min_value=0,max_value=90)
    classes_json=forms.CharField(widget=forms.HiddenInput())
class ConflictForm(forms.Form):
    conflict_date=forms.DateField(widget=forms.DateInput(attrs={'type':'date'}))
    class_name=forms.CharField(max_length=80)
    section=forms.CharField(max_length=30)
    day=forms.ChoiceField(choices=[])
    period_no=forms.IntegerField(min_value=1)
    absent_teacher=forms.CharField(max_length=120)
    replacement_teacher=forms.CharField(max_length=120)
    original_subject=forms.CharField(max_length=120)
    replacement_subject=forms.CharField(max_length=120)
    def __init__(self,*args,days=None,**kwargs):
        super().__init__(*args,**kwargs)
        if days: self.fields['day'].choices=[(d,d) for d in days]
