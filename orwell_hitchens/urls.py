from django.urls import path
from . import views

urlpatterns = [
    path('', views.evaluate_draft, name='orwell_evaluate'),
    path('evaluation/<int:evaluation_id>/', views.evaluation_detail, name='orwell_detail'),
    path('history/', views.evaluation_history, name='orwell_history'),
]

