# Study Planner

A web application to help students manage their study responsibilities and create optimized study plans.

## Features

- **Modules Management**: Add and manage study modules with assignments, due dates, and study requirements.
- **Study Schedule Configuration**: Set up your study schedule by selecting available days and hours.
- **Bank Holiday Integration**: Include British bank holidays in your study plan with customizable study hours.
- **Leave Day Planning**: Allocate leave days for studying with automatic optimization.
- **Interactive Calendar**: View your study plan in an interactive calendar format.
- **Multiple Export Options**: Export your study plan as PDF, HTML, or Excel.

## Technologies Used

- **Backend**: Python with Flask framework
- **Frontend**: HTML, CSS, JavaScript
- **UI Framework**: Bootstrap 5
- **Calendar**: FullCalendar.js
- **Data Processing**: Pandas for data manipulation
- **Export Functionality**: Support for Excel, PDF, and HTML exports

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/studyplanner.git
   cd studyplanner
   ```

2. Run the application using the single run script:
   ```
   python run.py
   ```

   This script will:
   - Check and install required dependencies automatically
   - Create necessary configuration directories and files
   - Start the Flask application
   - Open your browser to the application

3. Alternatively, you can install dependencies manually and run the app directly:
   ```
   pip install flask flask-wtf pandas openpyxl
   python app.py
   ```

## Usage

1. **Add Modules**: Start by adding your study modules, including the number of assignments, due dates, and study hours required.
2. **Configure Study Schedule**: Set up which days of the week you can study and how many hours are available on each day.
3. **Customize Holidays**: Select which bank holidays you can use for studying and specify available hours.
4. **Add Leave Days**: Specify how many leave days you plan to use for studying.
5. **View Study Plan**: Go to the Guide tab to see your personalized study plan in a calendar format.
6. **Export Plan**: Download your study plan in PDF, HTML, or Excel format for offline reference.

## Project Structure

- `run.py`: Single entry point script to run the application
- `app.py`: Main Flask application
- `forms.py`: Form definitions using Flask-WTF
- `utils.py`: Utility functions for calculating study plans and generating exports
- `templates/`: HTML templates
- `static/`: Static files (CSS, JavaScript)
- `config/`: Configuration files for modules, assignments, and study settings

## License

This project is licensed under the MIT License - see the LICENSE file for details.
