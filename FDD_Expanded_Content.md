# Function Design Document (FDD) - Expanded Content  
**Project Name:** In-House HR Portal  
**Document Version:** 1.0  
**Date:** 24-May-2025  
**Prepared By:** [Your Name or Team Name]  
**Reviewed By:** [Reviewer Name]  
**Approved By:** [Approver Name]  

---

## 1. Introduction

### 1.1 Purpose  
The purpose of this Function Design Document (FDD) is to provide a detailed description of the functional design of the HR Portal. This document outlines the design of the system’s functional modules, user interactions, and the overall architecture to ensure that the development team and stakeholders have a clear understanding of the system requirements and design approach. The FDD serves as a bridge between the requirements specification and the implementation, ensuring traceability and alignment with business goals.

### 1.2 Scope  
This document covers the design of the following key functional areas within the HR Portal: Employee Management, Leave Management, Attendance Tracking, Payroll Processing, Recruitment Management, and Reporting & Analytics. The scope includes user roles, workflows, data management, and integration points with internal and external systems. The design aims to support scalability, security, and usability for all users within the organization.

### 1.3 Definitions, Acronyms, Abbreviations  
- **HR:** Human Resources  
- **FDD:** Function Design Document  
- **EMP:** Employee  
- **UI:** User Interface  
- **API:** Application Programming Interface  
- **SRS:** Software Requirements Specification  

### 1.4 References  
- ISO/IEC 26514: Software and systems engineering — Documentation  
- ISO/IEC 25010: System and software quality models  
- Internal Project SRS v1.2  
- Wireframes & UI Mockups  
- Organizational HR Policies and Procedures  

---

## 2. Overall Description

### 2.1 Product Perspective  
The HR Portal is a web-based internal system designed to streamline HR operations. It features a modular architecture with distinct components for Employee Management, Leave Management, Attendance, Payroll, and Recruitment. The system supports role-based access control to ensure data security and appropriate user permissions. The portal integrates with internal mail systems and biometric devices to enhance functionality.

### 2.2 User Characteristics  
The primary users of the HR Portal include:  
- **HR/Admin Staff:** Manage employee records, leave approvals, payroll, and recruitment processes.  
- **Employees:** Access personal information, apply for leave, submit timesheets, and view pay slips.  
- **Managers:** Approve leave requests, assign tasks, and monitor team performance.  
- **Recruiters:** Manage job postings, screen candidates, and schedule interviews.  

### 2.3 Assumptions & Dependencies  
- Users have reliable access to the internal network and compatible devices.  
- The system depends on integration with biometric devices and internal email servers.  
- The portal is designed to be compatible with modern web browsers including Chrome, Edge, and Firefox.  
- External payroll or ERP system integration is planned for future phases and is out of scope for this release.  

---

## 3. Functional Design

### 3.1 Module: Employee Management  
This module allows HR staff to add, edit, view, and delete employee records. It supports uploading of employee documents such as identification and resumes. Employees can be assigned roles, departments, and reporting managers. The module also supports bulk import and export of employee data in CSV and Excel formats to facilitate data management.

### 3.2 Module: Leave Management  
Employees can apply for leave, view their leave balances, and cancel leave requests. The system supports configurable leave types and approval workflows, enabling managers to approve or reject leave applications. Real-time tracking of leave balances ensures accurate leave accounting.

### 3.3 Module: Attendance  
The attendance module records daily check-in and check-out times. It integrates with biometric and time-clock systems to automate attendance tracking. The system sends automated email alerts for absences and generates reports on late arrivals and absenteeism to assist management in monitoring attendance patterns.

### 3.4 Module: Payroll  
Payroll processing includes configuration of salary structures, automatic generation of salary slips, and management of bonuses, deductions, and tax calculations. The module supports statutory compliance with PF (Provident Fund) and ESI (Employee State Insurance) calculations and reporting.

### 3.5 Module: Recruitment  
Recruiters can manage job postings, parse and shortlist resumes, schedule interviews, and track candidate status through the recruitment pipeline from application to offer. The module facilitates efficient hiring workflows and candidate management.

### 3.6 Module: Reports & Analytics  
The reporting module enables generation of custom reports with filters by department, date, or role. Reports can be exported in PDF or Excel formats. Graphical dashboards provide visual insights into HR metrics such as employee demographics, leave trends, and recruitment status.

---

## 4. UI/UX Design Guidelines  
The HR Portal UI follows the internal design system, ensuring consistency in colors, fonts, and responsiveness. Accessibility standards (WCAG 2.1) are adhered to, making the portal usable by people with disabilities. The layout is mobile-friendly, with tabbed forms and modal dialogs to enhance usability and reduce clutter.

---

## 5. Non-Functional Requirements (Mapped to ISO/IEC 25010)  

| Quality Attribute | Description                          |  
|-------------------|----------------------------------|  
| Reliability       | The system guarantees 99.9% uptime to ensure availability for users.                      |  
| Usability         | The interface is intuitive, requiring minimal training for end-users.                    |  
| Performance       | Page load times are optimized to be under 2 seconds for a smooth user experience.       |  
| Security          | Role-based access control and data encryption at rest and in transit protect sensitive information. |  
| Maintainability   | The codebase is modular and well-documented, facilitating easy updates and API integrations. |  
| Portability       | The portal supports major browsers including Chrome, Edge, Firefox, and mobile browsers. |  

---

## 6. Interface Design

### 6.1 Internal Interfaces  
- The system interfaces with PostgreSQL or MySQL databases for data storage.  
- Biometric device APIs are used for attendance tracking integration.  
- Email and notification systems are integrated for alerts and communication.  

### 6.2 External Interfaces  
- Optional integration with third-party payroll or recruitment tools is supported for future expansion.  

---

## 7. Exception Handling  
The system includes robust exception handling mechanisms:  
- Input validations prevent invalid data entry.  
- Session timeouts ensure security by logging out inactive users.  
- Unauthorized access attempts redirect users to login pages.  
- User-friendly fallback messages are displayed during system downtime or errors.  

---

## 8. Data Design Overview  
The data design includes detailed Entity-Relationship (ER) diagrams illustrating the relationships between employees, leave records, attendance logs, payroll entries, and recruitment data. Field validations enforce data integrity by specifying lengths, data types, and mandatory fields. Sample datasets are used for testing and validation purposes.

---

## 9. Security Considerations  
Security is a top priority:  
- All logins use HTTPS with salted password hashes to protect credentials.  
- The system implements protections against CSRF, XSS, and SQL injection attacks.  
- Audit logs record all create, read, update, and delete (CRUD) operations for accountability and traceability.  

---

## 10. Appendices  

### Appendix A: Glossary  
A comprehensive glossary of terms and acronyms used throughout the document.

### Appendix B: Sample Screens  
Screenshots and mockups of key UI screens and workflows.

### Appendix C: Change Log  
A record of document revisions, authors, and approval dates.

---

# ISO Standard Formatting Guidelines for Google Docs

- **Font:** Times New Roman  
- **Font Size:** 12 pt  
- **Line Spacing:** 1.5 lines  
- **Margins:** 1 inch (2.54 cm) on all sides  
- **Header:** Document title and page number  
- **Footer:** Confidentiality statement or company name  
- **Headings:** Use consistent heading styles (Heading 1 for main sections, Heading 2 for subsections)  
- **Page Breaks:** Insert page breaks between major sections to ensure each topic starts on a new page  

---

# Instructions to Create Google Doc

1. Open Google Docs and create a new blank document.  
2. Set the font to Times New Roman, size 12, and line spacing to 1.5.  
3. Set page margins to 1 inch on all sides (File > Page setup).  
4. Copy the expanded content from this file section by section, pasting into the Google Doc.  
5. Apply heading styles to section titles (Heading 1 for main sections, Heading 2 for subsections).  
6. Insert page breaks before each main section to ensure one page per topic.  
7. Add header with document title and page number (Insert > Header & page number).  
8. Add footer with confidentiality statement or company name.  
9. Review the document for formatting consistency and save.  
10. Share the document with appropriate permissions and provide the shareable link.
