"""
URL configuration for dental_notes project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views

urlpatterns = [
    path('record/', views.speech_index, name='speech_index'),
    path('history/', views.history, name='history'),
    path('template/', views.template, name='template'),
    path('account/', views.account, name='account'),
    path('record/start-transcription/', views.start_transcription, name='start_transcription'),
    path('record/stop-transcription/', views.stop_transcription, name='stop_transcription'),
    path('record/generate-summary/', views.generate_summary, name='generate_summary'),
    path('record/generate-template-summary/', views.generate_template_summary, name='generate_template_summary'),
    path('record/save-note/', views.save_note, name='save_note'),
    path('record/note-detail/<int:note_id>/', views.note_detail, name='note_detail'),
    path('record/update-note/<int:note_id>/', views.update_note, name='update_note'),
    path('record/delete-note/<int:note_id>/', views.delete_note, name='delete_note'),
    path('account/update/', views.account_update, name='account_update'),
]
