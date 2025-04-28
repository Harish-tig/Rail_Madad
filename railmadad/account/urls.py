from django.urls import path
from . import views

urlpatterns = [
    path("", views.home ,name='home'),
    path("register/", views.register, name = 'register' ),
    path("verify/", views.verify, name = 'verify'),
    path("login/",views.login, name = 'login'),
    path('complaint/',views.raise_complaint, name = 'raise_complaint'),
    path('predict-complaint/',views.predict_complaint,name = 'auto_complaint' ),
    path('confirm-complaint',views.confirm_complaint,name= 'confirm_complaint')
]