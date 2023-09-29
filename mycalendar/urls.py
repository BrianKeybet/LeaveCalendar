from django.urls import path, include
from . import views
from django.conf import settings

urlpatterns = [
    path('calendar/', views.LeaveCalendarView.as_view(), name='calendar'),
    path('yearly-calendar/', views.YearlyLeaveCalendarView.as_view(), name='yearly_calendar'),
    path('leave_request_list/<str:date>/', views.LeaveRequestListView.as_view(), name='leave_request_list'),
    path('yearly_leave_dashboard/', views.YearlyLeaveDashboardView.as_view(), name='yearly_leave_dashboard'),
]

if settings.DEBUG:
    # import debug_toolbar
    urlpatterns += [
        path('__debug__', include('debug_toolbar.urls'))
    ]