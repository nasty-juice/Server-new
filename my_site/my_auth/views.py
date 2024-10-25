from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView, View

from .forms import StudentCardForm

# Create your views here.
def initial_auth_view(request):
    return render(request, 'my_auth/initial_auth_view.html')

class StudentCardAuthView(CreateView):
    form_class = StudentCardForm
    template_name = 'my_auth/student_card_auth_view.html'
    success_url = reverse_lazy('my_auth:initial_auth_view')
    
    # def form_valid(self, form):
    #     form.instance.user = self.request.user
    #     return super().form_valid(form)
    
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['student_card_image'] = self.request.user.student_card_image
    #     return context