import json
from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect, get_object_or_404
from .models import GeneralTimetable, ConflictRecord
from .forms import GeneralTimetableForm, ConflictForm
from .ga import generate_timetable

def admin_check(user): return user.is_authenticated and user.is_staff
class AdminLoginView(LoginView):
    template_name='timetable/login.html'
    redirect_authenticated_user=True
    def form_valid(self,form):
        if not form.get_user().is_staff:
            form.add_error(None,'This account is not authorized for administrator access.')
            return self.form_invalid(form)
        return super().form_valid(form)

@login_required
@user_passes_test(admin_check)
def dashboard(request):
    general=GeneralTimetable.objects.order_by('-created_at').first()
    recent=ConflictRecord.objects.order_by('-created_at')[:6]
    return render(request,'timetable/dashboard.html',{'general':general,'recent':recent})

@login_required
@user_passes_test(admin_check)
def general_timetable(request):
    latest=GeneralTimetable.objects.order_by('-created_at').first()
    if request.method=='POST':
        form=GeneralTimetableForm(request.POST)
        if form.is_valid():
            try:
                data=form.cleaned_data
                config={'academic_year':data['academic_year'],'days':[x.strip() for x in data['days'].split(',') if x.strip()],
                  'periods':data['periods'],'start_time':data['start_time'].strftime('%H:%M'),
                  'period_minutes':data['period_minutes'],'break_after':data['break_after'],
                  'break_minutes':data['break_minutes'],'classes':json.loads(data['classes_json'])}
                if not config['days'] or not config['classes']: raise ValueError('Add working days and at least one class.')
                schedule=generate_timetable(config)
                GeneralTimetable.objects.create(academic_year=config['academic_year'],config=config,timetable=schedule,created_by=request.user)
                messages.success(request,'Genetic Algorithm generated and saved the general timetable.')
                return redirect('general')
            except Exception as exc: messages.error(request,str(exc))
    else: form=GeneralTimetableForm()
    return render(request,'timetable/general.html',{'form':form,'latest':latest})

@login_required
@user_passes_test(admin_check)
def update_timetable(request):
    general=GeneralTimetable.objects.order_by('-created_at').first()
    if not general:
        messages.warning(request,'Create the general timetable first.')
        return redirect('general')
    days=general.config.get('days',[])
    if request.method=='POST':
        form=ConflictForm(request.POST,days=days)
        if form.is_valid():
            d=form.cleaned_data
            snapshot=json.loads(json.dumps(general.timetable))
            found=False
            for cls in snapshot:
                if cls['class_name']==d['class_name'] and cls['section']==d['section']:
                    for dayrow in cls['days']:
                        if dayrow['day']==d['day']:
                            p=d['period_no']-1
                            if p<0 or p>=len(dayrow['periods']): break
                            dayrow['periods'][p]={'subject':d['replacement_subject'],'teacher':d['replacement_teacher']}
                            found=True
            if found:
                ConflictRecord.objects.create(conflict_date=d['conflict_date'],class_name=d['class_name'],section=d['section'],
                  day=d['day'],period_no=d['period_no'],absent_teacher=d['absent_teacher'],replacement_teacher=d['replacement_teacher'],
                  original_subject=d['original_subject'],replacement_subject=d['replacement_subject'],
                  timetable_snapshot=snapshot,created_by=request.user)
                messages.success(request,'One-day timetable update saved in conflict history. The base timetable is unchanged.')
                return redirect('records')
            messages.error(request,'Class, section, day or period was not found in the base timetable.')
    else: form=ConflictForm(days=days)
    return render(request,'timetable/update.html',{'form':form,'classes':general.config.get('classes',[]),'general':general})

@login_required
@user_passes_test(admin_check)
def records(request):
    query=request.GET.get('date','')
    items=ConflictRecord.objects.order_by('-created_at')
    if query: items=items.filter(conflict_date=query)
    return render(request,'timetable/records.html',{'records':items,'query':query})

@login_required
@user_passes_test(admin_check)
def record_detail(request,pk):
    record=get_object_or_404(ConflictRecord,pk=pk)
    return render(request,'timetable/record_detail.html',{'record':record})
