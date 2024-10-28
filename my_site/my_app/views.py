from django.shortcuts import render, redirect
from django.urls import reverse
from .models import CustomUser
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy

# Create your views here.
def initial_view(request):
    return render(request, 'my_app/initial_view.html')

class UserListView(ListView):
    model = CustomUser
    # By default, the ListView class will use the following template:
    # <app_name>/<model_name>_list.html
    context_object_name = 'users_list'
    
class UserDetailView(DetailView):
    model = CustomUser
    # By default, the DetailView class will use the following template:
    # <app_name>/<model_name>_detail.html
    context_object_name = 'user'

# def redirect_to_auth_login(request):
#     return redirect(reverse('my_auth:accounts/login'))

# def redirect_to_auth_signup(request):
#     return redirect(reverse('my_auth:accounts/signup'))