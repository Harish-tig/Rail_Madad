from django.urls import path
from . import views

urlpatterns = [
    path('get-user-complaints/', views.get_user_all_complaints, name='user-complaints'),
    path('get-user-journey/', views.get_user_journey_details, name='get-user-journey'),
   
]