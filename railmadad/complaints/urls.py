from django.urls import path
from . import views

urlpatterns = [
    path('get-user-complaints/', views.get_user_all_complaints, name='user-complaints'),
   
]