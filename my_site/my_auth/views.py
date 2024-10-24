from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView, View

# Create your views here.

def initial_auth_view(request):
    return render(request, 'my_auth/initial_auth_view.html')


