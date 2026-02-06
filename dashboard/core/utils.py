from datetime import datetime
from django.contrib import messages


def date_formatter(request):
    date = request.GET.get('date-range', "")
    if date:
        try:
            date_parts = date.split("-")
            from_date = datetime.strptime(date_parts[0].strip(), "%m/%d/%Y").strftime("%Y-%m-%d")
            to_date = datetime.strptime(date_parts[1].strip(), "%m/%d/%Y").strftime("%Y-%m-%d")
            return from_date, to_date
        except Exception as e:
            messages.error(request, str(e))
    return None, None


