import gspread
from oauth2client.service_account import ServiceAccountCredentials
from django.core.management.base import BaseCommand
from datetime import date, time
from hr_app.tests import EmployeeManagementTests, LeaveManagementTests, ProjectManagementTests, TaskManagementTests, TimesheetManagementTests, HolidayManagementTests

# Main summary spreadsheet details
MAIN_SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/18a8V1Am5E0tuEwULD4CZgULqSVdRyfp6L0Kjb-KHA5c/edit?usp=sharing"
MAIN_SHEET_NAME = "Sheet1"
START_ROW_MAIN = 5

# Google Sheets API setup
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

def create_or_open_spreadsheet(title):
    try:
        # Try to open existing spreadsheet by title
        spreadsheet = client.open(title)
    except gspread.SpreadsheetNotFound:
        # Create new spreadsheet if not found
        spreadsheet = client.create(title)
    return spreadsheet

def share_spreadsheet_with_email(spreadsheet, email):
    # Share the spreadsheet with the given email with editor permission and notify the user
    spreadsheet.share(email, perm_type='user', role='writer', notify=True)

def make_spreadsheet_public(spreadsheet):
    # Make the spreadsheet accessible to anyone with the link
    spreadsheet.share(None, perm_type='anyone', role='reader', notify=False)

def update_module_spreadsheet(spreadsheet, test_data):
    sheet = spreadsheet.sheet1
    sheet.clear()
    header = ["Sr. #", "Test Id", "Role", "Module Name", "Test Cases", "Action to be Taken", "Url or Navigation or Process you followed", "Expected Result", "Actual Result", "Test Result"]
    sheet.insert_row(header, 1)
    next_row = 2
    for test in test_data:
        row = [next_row] + test
        sheet.insert_row(row, next_row)
        next_row += 1

def update_main_summary(module_rows):
    main_sheet = client.open_by_url(MAIN_SPREADSHEET_URL).worksheet(MAIN_SHEET_NAME)
    row_num = START_ROW_MAIN
    for row in module_rows:
        main_sheet.insert_row(row, row_num)
        row_num += 1

class Command(BaseCommand):
    help = 'Create separate spreadsheets for each module tests and update main summary spreadsheet'

    def handle(self, *args, **kwargs):
        # Example test data extraction for Employee Management module
        employee_tests = [
            ["EMP001", "Employee", "Employee Management", "test_employee_creation", "Verify employee creation with valid data", "Navigate to Employee List", "Employee created successfully", "", ""],
            ["EMP002", "Employee", "Employee Management", "test_employee_list_view", "Verify employee list view", "Access employee_list URL", "Employee list displayed with test user", "", ""]
        ]

        leave_tests = [
            ["LV001", "Employee", "Leave Management", "test_leave_application_creation", "Verify leave application creation", "Navigate to Leave Dashboard", "Leave application created with reason Vacation", "", ""],
            ["LV002", "Employee", "Leave Management", "test_leave_dashboard_view", "Verify leave dashboard view", "Access leave_dashboard URL", "Dashboard displays Annual Leave", "", ""],
            ["LV003", "HR", "Leave Management", "test_hr_approve_leave", "HR approves a pending leave application", "Login as HR > Navigate to Leave Dashboard > Approve leave", "Leave status updated to Approved", "", ""]
        ]

        project_tests = [
            ["PRJ001", "Project Manager", "Project Management", "test_project_creation", "Verify project creation", "Navigate to Project page", "Project created with name Test Project", "", ""],
            ["PRJ002", "Project Manager", "Project Management", "test_project_view", "Verify project view", "Access project URL with project id", "Project page displays Test Project", "", ""],
            ["PRJ003", "Project Manager", "Project Management", "test_project_update", "Verify project update", "Navigate to Update Project page", "Project details updated successfully", "", ""],
            ["PRJ004", "Project Manager", "Project Management", "test_project_history_view", "Verify project history view", "Navigate to Project History page", "Project history displayed with recent changes", "", ""],
            ["PRJ005", "Project Manager", "Project Management", "test_assign_task_to_team_member", "Assign task to team member", "Navigate to Task page > Assign task to team member", "Task assigned successfully", "", ""]
        ]

        task_tests = [
            ["TSK001", "Project Manager", "Task Management", "test_task_creation", "Verify task creation", "Navigate to Task page", "Task created with name Test Task", "", ""],
            ["TSK002", "Project Manager", "Task Management", "test_task_list_view", "Verify task list view", "Access task_list URL", "Task list displays Test Task", "", ""],
            ["TSK003", "Employee", "Task Management", "test_update_task_status", "Employee updates task status", "Navigate to Task List > Update task status", "Task status updated successfully", "", ""]
        ]

        timesheet_tests = [
            ["TSH001", "Employee", "Timesheet Management", "test_timesheet_creation", "Verify timesheet creation", "Navigate to Timesheet page", "Timesheet created with description Worked on testing", "", ""],
            ["TSH002", "Employee", "Timesheet Management", "test_timesheet_view", "Verify timesheet view", "Access view_timesheet URL", "Timesheet page displays Timesheet User", "", ""]
        ]

        holiday_tests = [
            ["HLD001", "N/A", "Holiday Management", "test_holiday_creation", "Verify holiday creation", "Navigate to Holiday Dashboard", "Holiday created with name Test Holiday", "", ""],
            ["HLD002", "N/A", "Holiday Management", "test_holiday_dashboard_view", "Verify holiday dashboard view", "Access holiday_dashboard URL", "Dashboard displays Test Holiday", "", ""]
        ]

        # Create or open spreadsheets for each module
        employee_spreadsheet = create_or_open_spreadsheet("Employee Management Tests")
        update_module_spreadsheet(employee_spreadsheet, employee_tests)
        share_spreadsheet_with_email(employee_spreadsheet, "kataranischal@gmail.com")
        make_spreadsheet_public(employee_spreadsheet)

        leave_spreadsheet = create_or_open_spreadsheet("Leave Management Tests")
        update_module_spreadsheet(leave_spreadsheet, leave_tests)
        share_spreadsheet_with_email(leave_spreadsheet, "kataranischal@gmail.com")
        make_spreadsheet_public(leave_spreadsheet)

        project_spreadsheet = create_or_open_spreadsheet("Project Management Tests")
        update_module_spreadsheet(project_spreadsheet, project_tests)
        share_spreadsheet_with_email(project_spreadsheet, "kataranischal@gmail.com")
        make_spreadsheet_public(project_spreadsheet)

        task_spreadsheet = create_or_open_spreadsheet("Task Management Tests")
        update_module_spreadsheet(task_spreadsheet, task_tests)
        share_spreadsheet_with_email(task_spreadsheet, "kataranischal@gmail.com")
        make_spreadsheet_public(task_spreadsheet)

        timesheet_spreadsheet = create_or_open_spreadsheet("Timesheet Management Tests")
        update_module_spreadsheet(timesheet_spreadsheet, timesheet_tests)
        share_spreadsheet_with_email(timesheet_spreadsheet, "kataranischal@gmail.com")
        make_spreadsheet_public(timesheet_spreadsheet)

        holiday_spreadsheet = create_or_open_spreadsheet("Holiday Management Tests")
        update_module_spreadsheet(holiday_spreadsheet, holiday_tests)
        share_spreadsheet_with_email(holiday_spreadsheet, "kataranischal@gmail.com")
        make_spreadsheet_public(holiday_spreadsheet)

        # Prepare main summary rows for each module
        module_rows = [
            ["Employee Management", "URL or Navigation Link for Employee Module", "Overall test report summary", employee_spreadsheet.url],
            ["Leave Management", "URL or Navigation Link for Leave Module", "Overall test report summary", leave_spreadsheet.url],
            ["Project Management", "URL or Navigation Link for Project Module", "Overall test report summary", project_spreadsheet.url],
            ["Task Management", "URL or Navigation Link for Task Module", "Overall test report summary", task_spreadsheet.url],
            ["Timesheet Management", "URL or Navigation Link for Timesheet Module", "Overall test report summary", timesheet_spreadsheet.url],
            ["Holiday Management", "URL or Navigation Link for Holiday Module", "Overall test report summary", holiday_spreadsheet.url]
        ]

        # Update main summary spreadsheet starting from row 5
        update_main_summary(module_rows)

        self.stdout.write(self.style.SUCCESS('Module test spreadsheets created and main summary updated.'))
