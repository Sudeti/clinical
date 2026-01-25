from django.urls import path
from . import views

urlpatterns = [
    path('', views.evaluate_draft, name='evaluate_draft'),
    path('comment/', views.generate_comment, name='generate_comment'),
    path('comment/<int:generation_id>/select/<int:option_number>/', views.select_comment_option, name='select_comment_option'),
    path('hypocrisy/', views.generate_hypocrisy_comment, name='generate_hypocrisy_comment'),
    path('sovereign-x/', views.generate_clinical_sovereign_x, name='generate_clinical_sovereign_x'),
    path('sovereign-x/<int:generation_id>/select/<int:option_number>/', views.select_sovereign_x_option, name='select_sovereign_x_option'),
]