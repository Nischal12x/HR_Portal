import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1b77ug9TvjYK3h3SnhgLmy2pJVt4LxFLnxAvelhRMldo/edit?usp=sharing"
SHEET_NAME = "Sheet1"

# Define expanded test data for Leave module with detailed test cases
leave_module_tests = [
    ["LV001", "Leave Management", "Employee applies for leave with valid data", "Employee applies for leave with all mandatory fields filled correctly", "Pass", "Navigate to Leave Module > Apply Leave > Fill form with valid data > Submit", "Leave application submitted and visible in dashboard", "Leave application submitted and visible in dashboard", "Pass"],
    ["LV002", "Leave Management", "Employee applies for leave with from_date after till_date", "Employee applies for leave with from_date later than till_date", "Fail", "Navigate to Leave Module > Apply Leave > Fill form with invalid dates > Submit", "Error message 'From date cannot be after till date.' displayed", "Error message displayed", "Pass"],
    ["LV003", "Leave Management", "HR approves leave application", "HR approves a pending leave application", "Pass", "Login as HR > Navigate to Leave Dashboard > Approve leave", "Leave status updated to Approved", "Leave status updated to Approved", "Pass"],
    ["LV004", "Leave Management", "HR creates new leave type", "HR creates a new leave type with all required fields", "Pass", "Login as HR > Navigate to Leave Settings > Add Leave Type > Submit", "New leave type created and visible in settings", "New leave type created and visible in settings", "Pass"],
    # Additional detailed test cases can be added here
]

def update_test_results(test_data):
    # Setup Google Sheets API client
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)

    # Open the spreadsheet and sheet
    sheet = client.open_by_url(SPREADSHEET_URL).worksheet(SHEET_NAME)

    # Clear existing data before updating
    sheet.clear()

    # Insert header row
    header = ["Sr. #", "Test Id", "Role", "Module Name", "Test Cases", "Action to be Taken", "Url or Navigation or Process you followed", "Expected Result", "Actual Result", "Test Result"]
    sheet.insert_row(header, 1)

    # Insert testing data
    next_row = 2
    for test in test_data:
        row = [next_row] + test
        sheet.insert_row(row, next_row)
        next_row += 1

def main():
    update_test_results(leave_module_tests)

if __name__ == "__main__":
    main()
