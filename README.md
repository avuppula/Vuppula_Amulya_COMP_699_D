# Campus IT Helpdesk Ticket Management System

## Overview

The Campus IT Helpdesk Ticket Management System is a web-based application built using Python and Streamlit. It is designed to centralize and streamline IT support requests within a university environment. The system replaces traditional methods such as emails, phone calls, and walk-ins with a structured digital platform for efficient issue tracking and resolution.

This application supports multiple user roles including students, faculty, staff, IT technicians, and administrators. It enables users to submit tickets, track their status, and communicate with IT teams, while technicians and administrators manage and monitor service operations.

---

## Features

### User Features

* Submit IT support tickets with title, description, category, and location
* Upload attachments such as screenshots and documents
* View and track ticket status in real time
* Add comments to tickets for updates or clarification
* Reopen resolved tickets within a 5-day window
* Cancel tickets before processing begins
* Search tickets using keywords or ticket ID

### Technician Features

* View and accept unassigned tickets based on priority
* Manage assigned tickets and update their status
* Add internal notes and public responses
* Reassign or escalate tickets to other technicians
* Set estimated completion time for tickets
* Monitor workload and prioritize tasks

### Administrator Features

* Manage user accounts (create, activate, deactivate)
* Define and manage ticket categories with default priorities
* Configure escalation rules based on priority levels
* Generate reports on ticket volume, resolution time, and performance
* Monitor technician workload and system performance
* Archive old tickets for system maintenance

### System Features

* Role-based authentication and access control
* Secure password storage using hashing
* Ticket history tracking and audit logs
* Notification system for ticket updates
* File attachment handling with size validation
* Dashboard analytics with visual reports
* CSV export functionality for reports

---

## Technology Stack

* Frontend: Streamlit
* Backend: Python
* Database: SQLite
* Data Processing: Pandas
* Visualization: Plotly

---

## Installation

Make sure Python 3.10 or higher is installed on your system.

Install required packages:

```bash
python -m pip install streamlit pandas sqlalchemy plotly
```

---

## Running the Application

Navigate to the project directory and run:

```bash
streamlit run helpdesk_app.py
```

The application will open automatically in your browser.

---

## Default Login Credentials

### Administrator

Email: [admin@university.edu](mailto:admin@university.edu)
Password: admin123

### Technician

Email: [john.tech@university.edu](mailto:john.tech@university.edu)
Password: tech123

### User

Email: [student1@university.edu](mailto:student1@university.edu)
Password: student123

---

## Project Structure

* helpdesk_app.py: Main application file containing UI and backend logic
* helpdesk.db: SQLite database (auto-created on first run)
* uploads/: Directory for storing uploaded files

---

## Key Functional Areas

* Ticket Management: Create, assign, update, and close tickets
* Communication: Comments and internal notes for collaboration
* Reporting: Analytics and exportable reports
* Security: Role-based access and session handling
* Performance Monitoring: SLA tracking and escalation rules

---

## Future Enhancements

* Integration with email and notification services
* REST API layer for scalability
* Improved authentication using OAuth or JWT
* Cloud storage for file attachments
* Pagination and advanced filtering for large datasets
* Mobile-responsive UI improvements

---

## Conclusion

This project demonstrates a complete end-to-end IT service management solution. It improves efficiency, transparency, and accountability in handling IT support requests. The system is scalable and can be extended further to meet enterprise-level requirements.

---
