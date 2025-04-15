from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
from forms import ModuleForm, StudyForm, AssignmentForm
from utils import calculate_study_plan, generate_excel, generate_pdf, generate_html
import os
import json
from datetime import datetime

app = Flask(__name__)

# Add current year to all templates for the footer
@app.context_processor
def inject_now():
    return {'now': datetime.now()}
app.config['SECRET_KEY'] = 'your-secret-key'

# Data storage (in a real app, this would be a database)
modules_data = []
assignments_data = []
study_settings = {}

# File paths for saving configuration
CONFIG_DIR = 'config'
MODULES_FILE = os.path.join(CONFIG_DIR, 'modules.json')
ASSIGNMENTS_FILE = os.path.join(CONFIG_DIR, 'assignments.json')
SETTINGS_FILE = os.path.join(CONFIG_DIR, 'settings.json')

# Create config directory if it doesn't exist
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

# Load saved configuration if available
def load_configuration():
    global modules_data, assignments_data, study_settings
    
    # Load modules
    if os.path.exists(MODULES_FILE):
        with open(MODULES_FILE, 'r') as f:
            modules_data = json.load(f)
    
    # Load assignments
    if os.path.exists(ASSIGNMENTS_FILE):
        with open(ASSIGNMENTS_FILE, 'r') as f:
            assignments_data = json.load(f)
    
    # Load study settings
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            study_settings = json.load(f)

# Save configuration
def save_configuration():
    # Save modules
    with open(MODULES_FILE, 'w') as f:
        json.dump(modules_data, f, indent=2)
    
    # Save assignments
    with open(ASSIGNMENTS_FILE, 'w') as f:
        json.dump(assignments_data, f, indent=2)
    
    # Save study settings
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(study_settings, f, indent=2)

# Load configuration at startup
load_configuration()

# Default bank holidays if not in settings
default_bank_holidays = [
    {"date": "2025-01-01", "name": "New Year's Day", "selected": False, "hours": 0},
    {"date": "2025-04-18", "name": "Good Friday", "selected": False, "hours": 0},
    {"date": "2025-04-21", "name": "Easter Monday", "selected": False, "hours": 0},
    {"date": "2025-05-05", "name": "Early May Bank Holiday", "selected": False, "hours": 0},
    {"date": "2025-05-26", "name": "Spring Bank Holiday", "selected": False, "hours": 0},
    {"date": "2025-08-25", "name": "Summer Bank Holiday", "selected": False, "hours": 0},
    {"date": "2025-12-25", "name": "Christmas Day", "selected": False, "hours": 0},
    {"date": "2025-12-26", "name": "Boxing Day", "selected": False, "hours": 0}
]

# Use bank holidays from settings if available, otherwise use defaults
bank_holidays = study_settings.get('bank_holidays', default_bank_holidays)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/modules', methods=['GET', 'POST'])
def modules():
    form = ModuleForm()
    if request.method == 'POST':
        module_data = request.json
        if module_data:
            # Add or update module
            for i, module in enumerate(modules_data):
                if module['id'] == module_data.get('id'):
                    modules_data[i] = module_data
                    break
            else:
                # New module
                if not module_data.get('id'):
                    module_data['id'] = len(modules_data) + 1
                modules_data.append(module_data)
            
            # Save configuration
            save_configuration()
            
            return jsonify({"success": True, "modules": modules_data})
        return jsonify({"success": False, "error": "Invalid data"})
    return render_template('modules.html', form=form, modules=modules_data)

@app.route('/delete_module/<int:module_id>', methods=['POST'])
def delete_module(module_id):
    global modules_data, assignments_data
    modules_data = [m for m in modules_data if m['id'] != module_id]
    assignments_data = [a for a in assignments_data if a['module_id'] != module_id]
    
    # Save configuration
    save_configuration()
    
    return jsonify({"success": True, "modules": modules_data})

@app.route('/assignments/<int:module_id>', methods=['GET', 'POST'])
def assignments(module_id):
    form = AssignmentForm()
    form.module_id.data = module_id
    
    # Find the module
    module = next((m for m in modules_data if m['id'] == module_id), None)
    if not module:
        return redirect(url_for('modules'))
    
    if request.method == 'POST':
        assignment_data = request.json
        if assignment_data:
            # Add or update assignment
            for i, assignment in enumerate(assignments_data):
                if assignment['id'] == assignment_data.get('id'):
                    assignments_data[i] = assignment_data
                    break
            else:
                # New assignment
                if not assignment_data.get('id'):
                    assignment_data['id'] = len(assignments_data) + 1
                assignment_data['module_id'] = module_id
                assignments_data.append(assignment_data)
            
            # Save configuration
            save_configuration()
            
            return jsonify({"success": True, "assignments": [a for a in assignments_data if a['module_id'] == module_id]})
        return jsonify({"success": False, "error": "Invalid data"})
    
    # Get assignments for this module
    module_assignments = [a for a in assignments_data if a['module_id'] == module_id]
    return render_template('assignments.html', form=form, module=module, assignments=module_assignments)

@app.route('/assignments/<int:module_id>/<int:assignment_id>', methods=['GET'])
def get_assignment(module_id, assignment_id):
    # Find the assignment
    assignment = next((a for a in assignments_data if a['id'] == assignment_id and a['module_id'] == module_id), None)
    if not assignment:
        return jsonify({"success": False, "error": "Assignment not found"})
    
    return jsonify({"success": True, "assignment": assignment})

@app.route('/delete_assignment/<int:assignment_id>', methods=['POST'])
def delete_assignment(assignment_id):
    global assignments_data
    # Get module_id before deleting
    assignment = next((a for a in assignments_data if a['id'] == assignment_id), None)
    if not assignment:
        return jsonify({"success": False, "error": "Assignment not found"})
    
    module_id = assignment['module_id']
    assignments_data = [a for a in assignments_data if a['id'] != assignment_id]
    
    # Save configuration
    save_configuration()
    
    return jsonify({
        "success": True, 
        "assignments": [a for a in assignments_data if a['module_id'] == module_id]
    })

@app.route('/study', methods=['GET', 'POST'])
def study():
    form = StudyForm()
    if request.method == 'POST':
        data = request.json
        if data:
            study_settings.update(data)
            
            # Save configuration
            save_configuration()
            
            return jsonify({"success": True, "settings": study_settings})
        return jsonify({"success": False, "error": "Invalid data"})
    return render_template('study.html', form=form, settings=study_settings, holidays=bank_holidays)

@app.route('/update_holidays', methods=['POST'])
def update_holidays():
    global bank_holidays
    data = request.json
    if data and 'holidays' in data:
        bank_holidays = data['holidays']
        
        # Save bank holidays in study settings
        study_settings['bank_holidays'] = bank_holidays
        save_configuration()
        
        return jsonify({"success": True, "holidays": bank_holidays})
    return jsonify({"success": False, "error": "Invalid data"})

@app.route('/guide')
def guide():
    if not modules_data or not study_settings:
        return render_template('guide.html', has_data=False)
    
    study_plan = calculate_study_plan(modules_data, study_settings, bank_holidays, assignments_data)
    return render_template('guide.html', has_data=True, study_plan=study_plan)

@app.route('/export/<format>')
def export(format):
    if not modules_data or not study_settings:
        return jsonify({"success": False, "error": "No data to export"})
    
    study_plan = calculate_study_plan(modules_data, study_settings, bank_holidays, assignments_data)
    
    if format == 'excel':
        file_path = generate_excel(study_plan)
        return send_file(file_path, as_attachment=True, download_name="study_plan.xlsx")
    elif format == 'pdf':
        file_path = generate_pdf(study_plan)
        return send_file(file_path, as_attachment=True, download_name="study_plan.pdf")
    elif format == 'html':
        file_path = generate_html(study_plan)
        return send_file(file_path, as_attachment=True, download_name="study_plan.html")
    else:
        return jsonify({"success": False, "error": "Invalid format"})

if __name__ == '__main__':
    app.run(debug=True)
