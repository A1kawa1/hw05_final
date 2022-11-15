from django.contrib.auth.views import LogoutView, LoginView
from django.urls import path
from users import views

app_name = 'users'

urlpatterns = [
    path(
        'logout/',
        LogoutView.as_view(template_name='users/logged_out.html'),
        name='logout'
    ),
    path(
        'login/',
        LoginView.as_view(template_name='users/login.html'),
        name='login'
    ),
    path(
        'signup/',
        views.SignUp.as_view(),
        name='signup'
    ),
    path(
        'password_change/',
        views.MyPasswordChangeView.as_view(),
        name='password_change'
    ),
    path(
        'password_change/done/',
        views.MyPasswordChangeDoneView.as_view(),
        name='password_change_done'
    )
]
