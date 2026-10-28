from django.urls import path
from . import views

app_name = 'mobile'
urlpatterns = [
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
