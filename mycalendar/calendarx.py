from datetime import datetime, timedelta
from calendar import monthcalendar

class Calendar:
    def __init__(self):
        self.year = datetime.now().year
        self.month = datetime.now().month
        self.day = datetime.now().day

    def formatmonth(self, year, month):
        calendar = monthcalendar(year, month)
        html = '<table>'
        html += '<tr><th>Sun</th><th>Mon</th><th>Tue</th><th>Wed</th><th>Thu</th><th>Fri</th><th>Sat</th></tr>'
        for week in calendar:
            html += '<tr>'
            for day in week:
                if day == 0:
                    html += '<td></td>'
                else:
                    html += '<td>{}</td>'.format(day)
            html += '</tr>'
        html += '</table>'
        return html

    def render(self):
        html = '<table>'
        html += '<tr><th>Sun</th><th>Mon</th><th>Tue</th><th>Wed</th><th>Thu</th><th>Fri</th><th>Sat</th></tr>'
        html += '</table>'
        return html
