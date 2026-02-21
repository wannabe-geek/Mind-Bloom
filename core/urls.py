from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('mood-checkin/', views.mood_checkin, name='mood_checkin'),
    path('journal/', views.journal, name='journal'),
    path('tasks/', views.tasks, name='tasks'),
    path('ai-chat/', views.ai_chat, name='ai_chat'),
    path('find-therapist/', views.find_therapist, name='find_therapist'),
    path('find-resources/', views.find_resources, name='find_resources'),
    path('self-help/', views.self_help, name='self_help'),
    path('connect-therapist/<int:therapist_id>/', views.connect_therapist, name='connect_therapist'),
    path('clinical-progress/<int:student_id>/', views.clinical_progress, name='clinical_progress'),
    path('messages/', views.messages_list, name='messages_list'),
    path('chat/<int:user_id>/', views.chat_session, name='chat_session'),
    path('settings/', views.settings, name='settings'),
    path('focus-timer/', views.focus_timer, name='focus_timer'),
    path('ai-mentor/', views.ai_mentor, name='ai_mentor'),
    path('register/', views.register, name='register'),
    
    # Admin Management
    path('admin-users/', views.admin_user_management, name='admin_users'),
    path('admin-moderation/', views.admin_moderation, name='admin_moderation'),
    path('admin-cms/', views.admin_cms, name='admin_cms'),
    path('admin-security/', views.admin_security, name='admin_security'),
    path('admin-ai-monitor/', views.admin_ai_monitor, name='admin_ai_monitor'),

    # Therapist Professional Portal
    path('therapist/profile/', views.therapist_profile_view, name='therapist_profile'),
    path('therapist/appointments/', views.therapist_appointments, name='therapist_appointments'),
    path('therapist/records/<int:student_id>/', views.therapist_student_records, name='therapist_records'),
    path('therapist/insights/', views.therapist_insights, name='therapist_insights'),
    path('therapist/crisis/', views.therapist_crisis, name='therapist_crisis'),
]
