from django.views.generic import CreateView
from django.contrib.auth.views \
    import PasswordChangeDoneView, PasswordChangeView
from django.urls import reverse_lazy
from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


class MyPasswordChangeView(PasswordChangeView):
    template_name = 'users/password_change_form.html'
    success_url = reverse_lazy('users:password_change_done')


class MyPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = 'users/password_change_done.html'
