from django.shortcuts import render
from django.views.generic import View
from .forms import LeaveRequestForm
from .calendarx import Calendar
from .models import LeaveRequest, Department
from datetime import datetime, timedelta
from django.utils.safestring import mark_safe
import calendar
from django.urls import reverse
from django.http import HttpResponse
from django.contrib import messages
# from django.core.cache import cache

from django.db.models import Max, QuerySet, Subquery, OuterRef


import random
import traceback

#Create your views here.
class LeaveCalendarView(View):
    def get(self, request):
        form = LeaveRequestForm()
        leave_requests = LeaveRequest.objects.all()
        year = request.GET.get('year', datetime.now().year)
        month = request.GET.get('month', datetime.now().month)
        cal = Calendar()
        # html_cal = cal.formatmonth(2020, 1, withyear=True)
        html_cal = cal.formatmonth(year, month)
        html_cal = html_cal.replace('<td ', '<td  width="150" height="150"')
        for leave_request in leave_requests:
            start_date = leave_request.start_date
            end_date = leave_request.end_date
            d = start_date
            delta = timedelta(days=1)
            while d <= end_date:
                if d.month == start_date.month:
                    html_cal = html_cal.replace('>{}</td>'.format(d.day), ' class="bg-danger text-light">{}</td>'.format(d.day))
                d += delta
        return render(request, 'mycalendar/leave_calendar.html', {'calendar': mark_safe(html_cal), 'form': form})

class YearlyLeaveCalendarView(View):
            
    def get(self, request):
        try:
            form = LeaveRequestForm()
            year = request.GET.get('year', datetime.now().year)
            year = int(year)
            department_id = request.GET.get('department', '')
            leave_requests = LeaveRequest.objects.filter(start_date__year=year, end_date__year=year)
            if department_id:
                leave_requests = leave_requests.filter(department_id=department_id).select_related('department')
            departments = Department.objects.all().prefetch_related('leave_requests')
            selected_department = int(department_id) if department_id else None
            cal = Calendar()
            
            d = '2000-01-01'
            month_calendars = {month: '' for month in range(1, 13)}

            # Create a dictionary to store the link colors for each name
            name_colors = {}

            for month in range(1, 13):
                month_name = calendar.month_name[month]
                month_html = f'<h3>{month_name}</h3>'
                month_html += cal.formatmonth(year, month)
                month_html = month_html.replace('<td ', '<td  width="150" height="150"')
                for leave_request in leave_requests:
                    start_date = leave_request.start_date
                    end_date = leave_request.end_date
                    d = start_date
                    delta = timedelta(days=1)
                    while d <= end_date:
                        if d.month == month:
                            date_str = d.strftime('%Y-%m-%d')
                            day_url = reverse('leave_request_list', kwargs={'date': date_str})
                            day_url += f'?department={department_id}'

                            name = leave_request.name

                            # Generate a random link color for each name
                            if name not in name_colors:
                                # Generate a random hex color code
                                color = '#' + ''.join(random.choices('0123456789ABCDEF', k=6))
                                name_colors[name] = color

                            # Set the link color inline using style attribute
                            day_html = f'<a href="{day_url}" style="color: {"red" if leave_requests.filter(start_date__lte=d, end_date__gte=d).count() > 1 else name_colors[name]}; font-weight: bold;">{d.day}</a>'


                            month_html = month_html.replace('>{}</td>'.format(d.day), '>{}</td>'.format(day_html))

                        d += delta
                month_calendars[month] = month_html

            calendar_list = [mark_safe(cal) for cal in month_calendars.values()]

            if department_id:

                ##The 2 raw queries below were replaced by the ones below it
                # leave_bal_view = LeaveRequest.objects.raw("CREATE OR REPLACE VIEW leave_bal_list AS SELECT name, MAX(end_date) FROM mycalendar_leaverequest GROUP BY name")
                # leave_requests = LeaveRequest.objects.raw(f"SELECT ml.id, lb.name, ml.leave_bal FROM leave_bal_list AS lb JOIN mycalendar_leaverequest AS ml ON lb.max = ml.end_date WHERE ml.department_id_id={department_id}")

                # First, define the subquery to get the latest end_date for each employee
                leave_bal_list = LeaveRequest.objects.filter(
                    department_id=department_id
                ).values('name').annotate(
                    max_end_date=Max('end_date')
                ).values('name', 'max_end_date')

                # Then, use the subquery to retrieve the latest leave balance for each employee
                leave_requests = LeaveRequest.objects.filter(
                    department_id=department_id,
                    end_date=Subquery(leave_bal_list.filter(
                        name=OuterRef('name')
                    ).values('max_end_date'))
                ).order_by('-end_date').values('name', 'leave_bal', 'id')

        except:
            return HttpResponse('Please pick a year')


        return render(request, 'mycalendar/yearly_leave_calendar.html', {
            'calendar_list': calendar_list, 
            'form': form, 
            'departments': departments, 
            'selected_department': selected_department,
            'year': year,
            'leave_requests': leave_requests
        })
        

class LeaveRequestListView(View):
    def get(self, request, **kwargs):
        date_str = kwargs.get('date')
        selected_department = request.GET.get('department', '')  # Department is obtained from the LeaveRequestListView url
        
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            leave_requests = LeaveRequest.objects.filter(start_date__lte=date, end_date__gte=date)
            
            if selected_department:
                leave_requests = leave_requests.filter(department_id=selected_department)
            
            names = [lr.name for lr in leave_requests]
            start_dates = [lr.start_date for lr in leave_requests]
            end_dates = [lr.end_date for lr in leave_requests]
            zipped_data = zip(names, start_dates, end_dates)
            context = {'zipped_data': zipped_data, 'date': date, 'selected_department': selected_department}
            return render(request, 'mycalendar/leave_request_list.html', context)
        else:
            # handle the case where no date was picked
            return HttpResponse('Please pick a date')
        
class YearlyLeaveDashboardView(View):

    def formatmonth(self, year, month):
        _, num_days_in_month = calendar.monthrange(year, month)

        # Get the day of the week for the first day of the month (0 for Monday, 6 for Sunday)
        first_day_of_month = datetime(year, month, 1)
        day_of_week = first_day_of_month.weekday()

        # Create a list to store the week headers ('Mon', 'Tue', 'Wed', ...)
        week_headers = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

        # Generate the week header row
        week_header_html = ''.join([f'<th>{header}</th>' for header in week_headers])
        week_header_row = f'<tr>{week_header_html}</tr>'

        # Initialize the HTML with the week header row
        html = f'<table>{week_header_row}<tr>'

        # Adjust the starting day of the month based on the day_of_week
        if day_of_week != 0:  # If the first day of the month is not a Sunday, add empty cells before it
            html += f'<td colspan="{day_of_week}"></td>'

        current_day_of_week = day_of_week

        # Variables to keep track of the current day of the week and the current day of the month
        current_day = 1

        # Generate the calendar rows for each week
        while current_day <= num_days_in_month:
            if current_day_of_week == 7:
                html += '</tr><tr>'
                current_day_of_week = 0

            html += f'<td class="day {current_day_of_week}">{current_day}</td>'
            current_day += 1
            current_day_of_week += 1

        # If the last day of the month is not a Saturday, add empty cells to complete the last week
        if current_day_of_week != 7:
            html += f'<td colspan="{7 - current_day_of_week}"></td>'

        # Close the table tag
        html += '</tr></table>'

        return html

    def get(self, request):
        message_list = [
        "The color red is used when multiple people have applied for leave on the same day.",
        "Each user is assigned a unique color for their leave entries.",
        "If the colors are not clear, you can refresh the page to get different colors.",
        "When you select a specific department, the page will reload and display a table in the bottom left corner showing the leave balances for that department.",
        "Clicking on a specific day's link will reload the page and show a table in the bottom right corner listing the users who have taken leave on that day."
        ]
        #The below loops through the messages only once during each session
        # current_message_index = request.session.get('current_message_index', 0)
        # if current_message_index < len(message_list):
            # current_message = message_list[current_message_index]
            # messages.info(request, current_message)
            # request.session['current_message_index'] = current_message_index + 1

        #This means that when current_message_index reaches the length of message_list, it will wrap around to 0 again, effectively creating a loop.
        current_message_index = request.session.get('current_message_index', 0)
        current_message = message_list[current_message_index % len(message_list)]
        messages.info(request, current_message)
        request.session['current_message_index'] = (current_message_index + 1) % len(message_list)


        print("View accessed.")
        try:
            form = LeaveRequestForm()
            year = request.GET.get('year', datetime.now().year)
            year = int(year)
            department_id = request.GET.get('department', '')
            selected_date = request.GET.get('date')
            print(f'selected_date:{selected_date}')

            leave_requests = LeaveRequest.objects.filter(start_date__year=year, end_date__year=year)
            if department_id:
                leave_requests = leave_requests.filter(department_id=department_id)

            # Convert to a queryset even if only a single object is returned
            leave_requests = leave_requests.all()

            # departments = Department.objects.all()
            departments = Department.objects.exclude(id__in=[9, 13, 29])
            selected_department = int(department_id) if department_id else None
            if selected_department:
                department = departments.filter(id=selected_department).first()
                if department:
                    department_name = department.name
            else:
                department_name = None

            cal = Calendar()

            d = '2000-01-01'
            month_calendars = {month: '' for month in range(1, 13)}

            # Create a dictionary to store the link colors for each name
            name_colors = {}

            for month in range(1, 13):
                month_name = calendar.month_name[month]
                month_html = f'<h3>{month_name}</h3>'
                month_html += self.formatmonth(year, month)
                month_html = month_html.replace('<td ', '<td  width="100" height="100"')

                # month_calendars[month] = (year, month, month_html)
                for leave_request in leave_requests:
                    start_date = leave_request.start_date
                    end_date = leave_request.end_date
                    d = start_date
                    delta = timedelta(days=1)
                    while d <= end_date:
                        if d.month == month:
                            date_str = d.strftime('%Y-%m-%d')
                            day_url = reverse('yearly_leave_dashboard') + f'?year={year}&department={department_id}&date={date_str}'

                            name = leave_request.name

                            # Generate a random link color for each name
                            if name not in name_colors:
                                # Generate a random hex color code
                                color = '#' + ''.join(random.choices('0123456789ABCDEF', k=6))
                                name_colors[name] = color

                            # Check if there are multiple leave requests for the same day using Python
                            same_day_leave_requests = [lr for lr in leave_requests if lr.start_date <= d and lr.end_date >= d]
                            is_multiple = len(same_day_leave_requests) > 1

                            # ... existing code ...

                            # Set the link color inline using style attribute
                            day_html = f'<a href="{day_url}" style="color: {"red" if is_multiple else name_colors[name]}; font-weight: bold;">{d.day}</a>'

                            # Set the link color inline using style attribute
                            # day_html = f'<a href="{day_url}" style="color: {"red" if leave_requests.filter(start_date__lte=d, end_date__gte=d).count() > 1 else name_colors[name]}; font-weight: bold;">{d.day}</a>'

                            month_html = month_html.replace('>{}</td>'.format(d.day), '>{}</td>'.format(day_html))

                        d += delta
                month_calendars[month] = month_html

            calendar_list = [mark_safe(cal) for cal in month_calendars.values()]
            # calendar_list = [mark_safe(cal[2]) for cal in month_calendars.values()]


            leave_requests_on_date = None

            if selected_date:
                # Filter leave requests for the selected date and department
                leave_requests_on_date = leave_requests.filter(start_date__lte=selected_date, end_date__gte=selected_date)

            if department_id:
                # First, define the subquery to get the latest end_date for each employee
                leave_bal_list = LeaveRequest.objects.filter(
                    department_id=department_id
                ).values('name').annotate(
                    max_end_date=Max('end_date')
                ).values('name', 'max_end_date')

                # Then, use the subquery to retrieve the latest leave balance for each employee
                leave_requests = LeaveRequest.objects.filter(
                    department_id=department_id,
                    end_date=Subquery(leave_bal_list.filter(
                        name=OuterRef('name')
                    ).values('max_end_date'))
                ).order_by('-end_date').values('name', 'leave_bal', 'id')

            return render(request, 'mycalendar/yearly_leave_dashboard.html', {
                'calendar_list': calendar_list,
                'form': form,
                'departments': departments,
                'department_name': department_name,
                'selected_department': selected_department,
                'year': year,
                'leave_requests': leave_requests,
                'selected_date': selected_date,
                'leave_requests_info': [(lr.name, lr.start_date, lr.end_date) for lr in leave_requests_on_date] if leave_requests_on_date else [],
            })

        except ValueError as e:
            traceback.print_exc()  # Print the traceback information
            print(str(e))
            return HttpResponse(f'Please pick a year: {str(e)}')





