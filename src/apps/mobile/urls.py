from django.urls import path
from . import views
from .workspace import workspace

app_name = 'mobile'
urlpatterns = [
    path('workspace/', workspace, name='workspace'),
    path('my-profile/', views.my_profile, name='my_profile'),
    path('profile-history/', views.profile_history, name='profile_history'),
    path('organization/', views.organization, name='organization'),
    path('profile-approvals/', views.profile_approvals, name='profile_approvals'),
    path('profile-requests/<int:pk>/decision/', views.profile_decision, name='profile_decision'),
    path('change-password/', views.change_password, name='change_password'),
    path('profile-requests/', views.profile_requests, name='profile_requests'),
    path('push-token/', views.push_token, name='push_token'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('me/', views.me, name='me'),
    path('attendance/', views.attendance, name='attendance'),
    path('leaves/', views.leaves, name='leaves'),
    path('leave-options/', views.leave_options, name='leave_options'),
    path('approvals/', views.approvals, name='approvals'),
    path('leaves/<int:pk>/decision/', views.decision, name='decision'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:pk>/read/', views.notification_read, name='notification_read'),
]
