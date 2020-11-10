import json
from datetime import datetime
from urllib import parse

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.timezone import make_aware, now
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, FormView
from django.forms import inlineformset_factory


from .forms import ExperimentCode, UserRegisterForm
from .models import Experiment, Subject, Trial, User, Keypress, Block


@method_decorator([login_required], name='dispatch')
class Profile(DetailView):
    model = User
    template_name = 'gestureApp/profile.html'

    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["experiments"] = self.request.user.experiments.all()
        return context
    

class SignUpView(CreateView):
  template_name = 'gestureApp/register.html'
  success_url = reverse_lazy('gestureApp:profile')
  form_class = UserRegisterForm


# Create your views here.
def experiment(request):
    form = ExperimentCode(request.GET)
    if form.is_valid():
        code = form.cleaned_data['code']
        experiment = get_object_or_404(Experiment, pk=code)
        return render(request, 'gestureApp/experiment.html', {
            'experiment': experiment,
            'blocks': list(experiment.blocks.all().values())
            })
    else:
        form = ExperimentCode()
        return render(request, 'gestureApp/home.html', {
            'form':form,
            'error_message': 'Form invalid'
            })
    

def home(request):
    form = ExperimentCode()
    return render(request, 'gestureApp/home.html', {'form':form})

def create_trials(request):
    data = json.loads(request.body)
    exp_code = data.get('experiment')
    print(exp_code)
    experiment = get_object_or_404(Experiment, pk=exp_code)
    
    # Create a new subject
    subject = Subject(age=25)
    subject.save()
    # Save the trials to database.
    experiment_trials = json.loads(data.get('experiment_trials'))
    for i,block in enumerate(experiment_trials):
        for trial in block:
            t = Trial(
                block=experiment.blocks.all()[i],
                subject=subject,
                started_at=make_aware(datetime.fromtimestamp(trial['started_at']/1000)))
            t.save()
            for keypress in trial['keypresses']:
                value = keypress['value']
                timestamp = keypress['timestamp']
                keypress = Keypress(trial=t, value=value, timestamp=make_aware(datetime.fromtimestamp(timestamp/1000)))
                keypress.save()
    
    # Create response
    data = {}
    return JsonResponse(data)

@login_required
def create_experiment(request):
    if request.method == "POST":
        exp_info = json.loads(request.body)
        experiment = Experiment.objects.create(name=exp_info['name'], creator=request.user)
        for block in exp_info['blocks']:
            block_obj = Block(
                experiment=experiment, 
                sequence=block['sequence'],
                max_time_per_trial=block['max_time_per_trial'],
                resting_time=block['resting_time'],
                type=Block.BlockTypes(block['block_type']),
                max_time=block['max_time'],
                num_trials=block['num_trials']
                )
            block_obj.full_clean()
            block_obj.save()
    return render(request, 'gestureApp/create_experiment.html', {})
