from django.urls import path
from . import views

urlpatterns = [
    path('', views.evaluate_draft, name='evaluate_draft'),
    path('comment/', views.generate_comment, name='generate_comment'),
    path('comment/<int:generation_id>/select/<int:option_number>/', views.select_comment_option, name='select_comment_option'),
]