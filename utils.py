import pandas as pd
import os
from datetime import datetime, timedelta
import calendar
import tempfile

def calculate_study_plan(modules, study_settings, bank_holidays, assignments_data=[]):
    """
    Calculate a study plan based on module data, assignments, and study settings
    
    Args:
        modules: List of module dictionaries
        study_settings: Dictionary of study settings
        bank_holidays: List of bank holiday dictionaries
        assignments_data: List of assignment dictionaries
    
    Returns:
        Dictionary with dates as keys and study tasks as values
    """
    # Initialize empty study plan
    study_plan = {}
    
    # Get study days and hours
    study_days = study_settings.get('study_days', {})
    leave_days = study_settings.get('leave_days', 0)
    
    # Convert bank holidays to a dict for easier lookup
    holiday_dict = {}
    for holiday in bank_holidays:
        if holiday.get('selected'):
            holiday_dict[holiday['date']] = {
                'name': holiday['name'],
                'hours': holiday['hours']
            }
    
    # Calculate start date (today)
    start_date = datetime.now().date()
    
    # If there are no assignments, use the old method with modules
    if not assignments_data:
        # Sort modules by due date (for backward compatibility)
        sorted_modules = sorted(modules, key=lambda x: datetime.strptime(x.get('due_date', '2099-12-31'), '%Y-%m-%d'))
        
        # Calculate end date (latest due date + 1 month for buffer)
        if sorted_modules and 'due_date' in sorted_modules[-1]:
            latest_due_date = datetime.strptime(sorted_modules[-1]['due_date'], '%Y-%m-%d').date()
            end_date = latest_due_date + timedelta(days=30)
        else:
            end_date = start_date + timedelta(days=90)  # Default 3 months if no modules
            
        # Generate all dates between start and end
        current_date = start_date
        all_dates = []
        while current_date <= end_date:
            all_dates.append(current_date)
            current_date += timedelta(days=1)
        
        # Allocate leave days (if any)
        leave_day_dates = allocate_leave_days(all_dates, leave_days, holiday_dict, study_days)
        
        # For each module, calculate study hours needed and distribute (backward compatibility)
        for module in sorted_modules:
            if 'due_date' in module:  # Skip modules without due dates
                module_name = module['name']
                assignments = int(module.get('assignments', 1))
                due_date = datetime.strptime(module['due_date'], '%Y-%m-%d').date()
                days_before = int(module['days_before'])
                
                # Calculate submission date (due date minus days_before)
                submission_date = due_date - timedelta(days=days_before)
                
                # For backward compatibility, use a default value if hours_required is not present
                hours_per_assignment = float(module.get('hours_required', 5))
                
                # Calculate total hours needed
                total_hours_needed = assignments * hours_per_assignment
                
                # Distribute study hours
                distribute_study_hours(
                    study_plan, module_name, total_hours_needed, 
                    start_date, submission_date, due_date, 
                    all_dates, holiday_dict, leave_day_dates, study_days
                )
    else:
        # Sort all assignments by due date (earliest first)
        all_assignments = sorted(assignments_data, key=lambda x: datetime.strptime(x['due_date'], '%Y-%m-%d'))
        
        # Calculate end date (latest assignment due date + 1 month for buffer)
        if all_assignments:
            latest_due_date = datetime.strptime(all_assignments[-1]['due_date'], '%Y-%m-%d').date()
            end_date = latest_due_date + timedelta(days=30)
        else:
            end_date = start_date + timedelta(days=90)  # Default 3 months if no assignments
        
        # Generate all dates between start and end
        current_date = start_date
        all_dates = []
        while current_date <= end_date:
            all_dates.append(current_date)
            current_date += timedelta(days=1)
        
        # Allocate leave days (if any)
        leave_day_dates = allocate_leave_days(all_dates, leave_days, holiday_dict, study_days)
        
        # Get all available study days
        available_study_days = []
        for date in all_dates:
            day_name = date.strftime('%A').lower()
            date_str = date.strftime('%Y-%m-%d')
            
            # Check if it's a study day, holiday, or leave day
            hours_available = 0
            
            if date_str in holiday_dict:
                hours_available = holiday_dict[date_str]['hours']
                day_type = 'holiday'
            elif date in leave_day_dates:
                hours_available = 6  # Default 6 hours for leave days
                day_type = 'leave'
            else:
                hours_available = study_days.get(day_name, 0)
                day_type = 'regular'
            
            if hours_available > 0:
                available_study_days.append({
                    'date': date,
                    'hours': hours_available,
                    'type': day_type
                })
        
        # Sort available days by date
        available_study_days.sort(key=lambda x: x['date'])
        
        # For each assignment (in order of due date)
        for assignment in all_assignments:
            # Find the module
            module_id = assignment['module_id']
            module = next((m for m in modules if m['id'] == module_id), None)
            if not module:
                continue
                
            module_name = module['name']
            days_before = int(module['days_before'])
            assignment_name = assignment['name']
            due_date = datetime.strptime(assignment['due_date'], '%Y-%m-%d').date()
            
            # Calculate submission date (due date minus days_before)
            submission_date = due_date - timedelta(days=days_before)
            
            # Get study and submission hours for this assignment
            study_hours = assignment.get('study_hours', 0)
            submission_hours = assignment.get('submission_hours', 0)
            
            # Calculate total hours needed for this assignment
            hours_needed = study_hours + submission_hours
            
            # Find available days for this assignment (before submission date)
            assignment_available_days = [
                day for day in available_study_days 
                if day['date'] <= submission_date and 
                day['date'] not in [d['date'] for d in study_plan.values() if 'date' in d]
            ]
            
            # Distribute hours across available days
            hours_remaining = hours_needed
            for day in assignment_available_days:
                if hours_remaining <= 0:
                    break
                    
                date_str = day['date'].strftime('%Y-%m-%d')
                hours_for_day = min(day['hours'], hours_remaining)
                hours_remaining -= hours_for_day
                
                # Determine if this is a study day or submission day
                # Prioritize study hours first, then submission hours
                original_study_hours = assignment.get('study_hours', 0)
                original_submission_hours = assignment.get('submission_hours', 0)
                
                if study_hours > 0:
                    task_type = "Study"
                    study_hours -= hours_for_day
                    hours_left = study_hours
                else:
                    task_type = "Submission"
                    submission_hours -= hours_for_day
                    hours_left = submission_hours
                
                # Add to study plan (only one assignment per day)
                study_plan[date_str] = {
                    'date': day['date'],
                    'module': f"{module_name} - {assignment_name} ({task_type})",
                    'hours': hours_for_day,
                    'days_to_deadline': (due_date - day['date']).days,
                    'day_type': day['type'],
                    'hours_left': hours_left,
                    'hours_type': task_type,
                    'original_study_hours': original_study_hours,
                    'original_submission_hours': original_submission_hours
                }
                
                # Remove this day from available days for other assignments
                available_study_days = [d for d in available_study_days if d['date'] != day['date']]
    
    # Convert study plan to the expected format
    formatted_study_plan = {}
    for date_str, task in study_plan.items():
        if 'date' in task:  # New format
            task_data = {
                'module': task['module'],
                'hours': task['hours'],
                'days_to_deadline': task['days_to_deadline'],
                'day_type': task['day_type']
            }
            
            # Add hours left if available
            if 'hours_left' in task:
                task_data['hours_left'] = task['hours_left']
                task_data['hours_type'] = task['hours_type']
            
            formatted_study_plan[date_str] = [task_data]
        else:  # Old format (for backward compatibility)
            formatted_study_plan[date_str] = task
    
    return formatted_study_plan

def allocate_leave_days(all_dates, leave_days, holiday_dict, study_days):
    """Helper function to allocate leave days"""
    leave_day_dates = []
    if leave_days > 0:
        # Find suitable dates for leave (prefer weekdays that aren't already study days)
        potential_leave_days = []
        for date in all_dates:
            day_name = date.strftime('%A').lower()
            date_str = date.strftime('%Y-%m-%d')
            
            # Skip if it's a holiday or already a study day
            if date_str in holiday_dict or study_days.get(day_name, 0) > 0:
                continue
            
            # Prefer weekdays
            if date.weekday() < 5:  # Monday to Friday
                potential_leave_days.append(date)
        
        # Take the first N days as leave days
        leave_day_dates = potential_leave_days[:leave_days]
    
    return leave_day_dates

def distribute_study_hours(study_plan, task_name, total_hours_needed, start_date, submission_date, due_date, 
                          all_dates, holiday_dict, leave_day_dates, study_days):
    """Helper function to distribute study hours for a task"""
    # Find available study days before submission date
    available_study_days = []
    for date in all_dates:
        if date >= start_date and date <= submission_date:
            day_name = date.strftime('%A').lower()
            date_str = date.strftime('%Y-%m-%d')
            
            # Check if it's a study day, holiday, or leave day
            hours_available = 0
            
            if date_str in holiday_dict:
                hours_available = holiday_dict[date_str]['hours']
                day_type = 'holiday'
            elif date in leave_day_dates:
                hours_available = 6  # Default 6 hours for leave days
                day_type = 'leave'
            else:
                hours_available = study_days.get(day_name, 0)
                day_type = 'regular'
            
            if hours_available > 0:
                available_study_days.append({
                    'date': date,
                    'hours': hours_available,
                    'type': day_type
                })
    
    # Sort by date
    available_study_days.sort(key=lambda x: x['date'])
    
    # Distribute hours across available days
    hours_remaining = total_hours_needed
    for day in available_study_days:
        if hours_remaining <= 0:
            break
            
        date_str = day['date'].strftime('%Y-%m-%d')
        hours_for_day = min(day['hours'], hours_remaining)
        hours_remaining -= hours_for_day
        
        # Add to study plan
        if date_str not in study_plan:
            study_plan[date_str] = []
            
        days_to_deadline = (due_date - day['date']).days
        
        study_plan[date_str].append({
            'module': task_name,
            'hours': hours_for_day,
            'days_to_deadline': days_to_deadline,
            'day_type': day['type']
        })
    
    return study_plan

def generate_excel(study_plan):
    """Generate Excel file from study plan"""
    # Convert study plan to DataFrame
    data = []
    for date_str, tasks in study_plan.items():
        for task in tasks:
            task_data = {
                'Date': date_str,
                'Module': task['module'],
                'Hours': task['hours'],
                'Days to Deadline': task['days_to_deadline'],
                'Day Type': task['day_type'].capitalize()
            }
            
            # Add hours left if available
            if 'hours_left' in task:
                if 'Study' in task['module']:
                    task_data['Hours Left'] = f"{task['hours_left']} hours left to study"
                else:
                    task_data['Hours Left'] = f"{task['hours_left']} hours left to submit"
            
            data.append(task_data)
    
    df = pd.DataFrame(data)
    
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix='.xlsx')
    os.close(fd)
    
    # Write to Excel
    df.to_excel(path, index=False)
    
    return path

def generate_pdf(study_plan):
    """Generate PDF file from study plan"""
    # For simplicity, we'll generate an HTML file and convert it to PDF
    html_content = generate_html_content(study_plan)
    
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix='.pdf')
    os.close(fd)
    
    # In a real application, you would use a library like WeasyPrint to convert HTML to PDF
    # For now, we'll just write the HTML to the file
    with open(path, 'w') as f:
        f.write(html_content)
    
    return path

def generate_html(study_plan):
    """Generate HTML file from study plan"""
    html_content = generate_html_content(study_plan)
    
    # Create a temporary file
    fd, path = tempfile.mkstemp(suffix='.html')
    os.close(fd)
    
    # Write HTML to file
    with open(path, 'w') as f:
        f.write(html_content)
    
    return path

def generate_html_content(study_plan):
    """Generate HTML content from study plan with calendar format"""
    # Group tasks by month and year
    months_data = {}
    
    for date_str, tasks in study_plan.items():
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        month_year = date_obj.strftime('%B %Y')
        day = date_obj.day
        
        if month_year not in months_data:
            months_data[month_year] = {
                'year': date_obj.year,
                'month': date_obj.month,
                'days': {}
            }
        
        months_data[month_year]['days'][day] = tasks
    
    # Generate HTML
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Study Plan Calendar</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 20px; 
                color: #333;
            }
            h1 { 
                color: #2c3e50; 
                text-align: center;
                margin-bottom: 30px;
            }
            h2 {
                color: #3498db;
                margin-top: 40px;
                margin-bottom: 15px;
                border-bottom: 2px solid #3498db;
                padding-bottom: 5px;
            }
            .calendar {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 30px;
            }
            .calendar th {
                background-color: #3498db;
                color: white;
                text-align: center;
                padding: 10px;
                font-weight: bold;
            }
            .calendar td {
                border: 1px solid #ddd;
                padding: 10px;
                height: 100px;
                width: 14.28%;
                vertical-align: top;
            }
            .calendar .day-number {
                font-weight: bold;
                font-size: 1.2em;
                margin-bottom: 5px;
                text-align: right;
            }
            .calendar .empty {
                background-color: #f9f9f9;
            }
            .task {
                margin-bottom: 5px;
                padding: 5px;
                border-radius: 3px;
                font-size: 0.9em;
            }
            .task.holiday {
                background-color: #ffcccc;
            }
            .task.leave {
                background-color: #ccffcc;
            }
            .task.regular {
                background-color: #cce5ff;
            }
            .hours {
                font-weight: bold;
            }
            .days-to-deadline {
                font-style: italic;
                font-size: 0.8em;
            }
            .legend {
                margin-top: 20px;
                margin-bottom: 40px;
                text-align: center;
            }
            .legend-item {
                display: inline-block;
                margin: 0 15px;
            }
            .legend-color {
                display: inline-block;
                width: 20px;
                height: 20px;
                margin-right: 5px;
                vertical-align: middle;
                border-radius: 3px;
            }
            .legend-regular {
                background-color: #cce5ff;
            }
            .legend-holiday {
                background-color: #ffcccc;
            }
            .legend-leave {
                background-color: #ccffcc;
            }
            @media print {
                .calendar {
                    page-break-inside: avoid;
                }
                h2 {
                    page-break-before: always;
                }
                h2:first-of-type {
                    page-break-before: avoid;
                }
            }
        </style>
    </head>
    <body>
        <h1>Study Plan Calendar</h1>
        
        <div class="legend">
            <div class="legend-item"><span class="legend-color legend-regular"></span> Regular Study Day</div>
            <div class="legend-item"><span class="legend-color legend-holiday"></span> Holiday</div>
            <div class="legend-item"><span class="legend-color legend-leave"></span> Leave Day</div>
        </div>
    """
    
    # Sort months chronologically
    sorted_months = sorted(months_data.items(), key=lambda x: (x[1]['year'], x[1]['month']))
    
    for month_year, data in sorted_months:
        year = data['year']
        month = data['month']
        
        # Create calendar for this month
        html += f"<h2>{month_year}</h2>"
        html += """<table class="calendar">
            <tr>
                <th>Sunday</th>
                <th>Monday</th>
                <th>Tuesday</th>
                <th>Wednesday</th>
                <th>Thursday</th>
                <th>Friday</th>
                <th>Saturday</th>
            </tr>
        """
        
        # Get first day of month and number of days
        first_day = datetime(year, month, 1)
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        
        num_days = last_day.day
        first_weekday = first_day.weekday()  # Monday is 0, Sunday is 6
        first_weekday = (first_weekday + 1) % 7  # Adjust to make Sunday 0
        
        # Generate calendar grid
        day_counter = 1
        html += "<tr>"
        
        # Empty cells for days before the 1st
        for i in range(first_weekday):
            html += '<td class="empty"></td>'
        
        # Fill in the days
        current_weekday = first_weekday
        while day_counter <= num_days:
            if current_weekday == 0 and day_counter != 1:
                html += "</tr><tr>"
            
            html += f'<td>'
            html += f'<div class="day-number">{day_counter}</div>'
            
            # Add tasks for this day
            if day_counter in data['days']:
                tasks = data['days'][day_counter]
                for task in tasks:
                    task_class = task['day_type']
                    module_name = task['module']
                    hours = task['hours']
                    days_to_deadline = task['days_to_deadline']
                    
                    # Add hours left if available
                    hours_left_html = ""
                    if 'hours_left' in task:
                        if 'Study' in module_name:
                            hours_left_html = f'<span class="hours-left">({task["hours_left"]} hrs left to study)</span>'
                        else:
                            hours_left_html = f'<span class="hours-left">({task["hours_left"]} hrs left to submit)</span>'
                    
                    html += f"""
                    <div class="task {task_class}">
                        {module_name}<br>
                        <span class="hours">{hours} hrs</span>
                        <span class="days-to-deadline">({days_to_deadline} days to deadline)</span>
                        {hours_left_html}
                    </div>
                    """
            
            html += '</td>'
            
            day_counter += 1
            current_weekday = (current_weekday + 1) % 7
        
        # Empty cells for days after the last day
        for i in range(current_weekday, 7):
            html += '<td class="empty"></td>'
        
        html += "</tr></table>"
    
    html += """
    </body>
    </html>
    """
    
    return html
