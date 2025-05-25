# Function Design Document (FDD)  
**Project Name:** In-House HR Portal  
**Document Version:** 1.0  
**Date:** 24-May-2025  
**Prepared By:** [Your Name or Team Name]  
**Reviewed By:** [Reviewer Name]  
**Approved By:** [Approver Name]  

---

## 1. Introduction

### 1.1 Purpose  
Define the design of the HR Portal’s functional modules and user interactions.

### 1.2 Scope  
Covers Employee Management, Leave Management, Attendance, Payroll, Recruitment, and Reports within the organization.

### 1.3 Definitions, Acronyms, Abbreviations  
- **HR:** Human Resources  
- **FDD:** Function Design Document  
- **EMP:** Employee  
- **UI:** User Interface  

### 1.4 References  
- ISO/IEC 26514: Software and systems engineering — Documentation  
- ISO/IEC 25010: System and software quality models  
- Internal Project SRS v1.2  
- Wireframes & UI Mockups  

---

## 2. Overall Description

### 2.1 Product Perspective  
- Web-based internal HR system  
- Modular design: Employee, Leave, Attendance, Payroll, Recruitment  
- Role-based access  

### 2.2 User Characteristics  
- HR/Admin staff  
- Employees  
- Managers  
- Recruiters  

### 2.3 Assumptions & Dependencies  
- Internal network access  
- Integrated with internal mail system  
- Compatible with modern browsers  

---

## 3. Functional Design

### 3.1 Module: Employee Management  
- Add/Edit/View/Delete employee records  
- Upload documents (e.g., ID, resume)  
- Assign roles, departments, and reporting managers  
- Import/Export employee data (CSV, Excel)  

### 3.2 Module: Leave Management  
- Apply/View/Cancel leave  
- Leave approval workflows  
- Leave type configuration  
- Real-time leave balance tracking  

### 3.3 Module: Attendance  
- Daily check-in/check-out  
- Integration with biometric/time-clock systems  
- Auto-email alerts for absences  
- Reports on late arrivals and absentees  

### 3.4 Module: Payroll  
- Salary structure configuration  
- Auto salary slip generation  
- Bonus, deduction, and tax configuration  
- PF/ESI calculation and reporting  

### 3.5 Module: Recruitment  
- Job post management  
- Resume parsing & shortlisting  
- Interview scheduling  
- Status tracking (Applied → Interview → Offer)  

### 3.6 Module: Reports & Analytics  
- Custom report generation  
- Export reports (PDF, Excel)  
- Filters by department, date, or role  
- Graphical dashboards  

---

## 4. UI/UX Design Guidelines  
- Follow internal design system (colors, fonts, responsiveness)  
- Accessibility (WCAG 2.1 compliant)  
- Mobile-friendly layout  
- Tabbed forms and modals for better usability  

---

## 5. Non-Functional Requirements (Mapped to ISO/IEC 25010)  

| Quality Attribute | Description                          |  
|-------------------|----------------------------------|  
| Reliability       | 99.9% uptime                      |  
| Usability         | Minimal training required, intuitive interface |  
| Performance       | Page load time < 2s               |  
| Security          | Role-based access, data encryption at rest and transit |  
| Maintainability   | Modular codebase, documented APIs |  
| Portability       | Supports Chrome, Edge, Firefox, mobile browsers |  

---

## 6. Interface Design

### 6.1 Internal Interfaces  
- Database (PostgreSQL/MySQL)  
- Biometric device APIs  
- Email/Notification system  

### 6.2 External Interfaces  
- Optional integration with third-party payroll or recruitment tools  

---

## 7. Exception Handling  
- Invalid input validations  
- Session timeouts  
- Unauthorized access redirection  
- System down fallback messages  

---

## 8. Data Design Overview  
- Entity-Relationship (ER) Diagrams  
- Field validations (lengths, data types)  
- Sample datasets  

---

## 9. Security Considerations  
- Encrypted login (HTTPS + salted password hashes)  
- CSRF/XSS/SQL injection prevention  
- Audit logs for all CRUD operations  

---

## 10. Appendices  

### Appendix A: Glossary  

### Appendix B: Sample Screens  

### Appendix C: Change Log
