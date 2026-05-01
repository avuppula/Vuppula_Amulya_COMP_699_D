# Install Command

# python -m pip install streamlit pandas sqlalchemy plotly

#admin ----> username: admin@university.edu    and   Password:  admin123

#technician ----> username: john.tech@university.edu    and   Password:  tech123

#user ----> username: student1@university.edu    and   Password:  student123

# Filename: helpdesk_app.py

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import hashlib
import io
import base64
from pathlib import Path

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('helpdesk.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.insert_default_data()
    
    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users(
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ticket_categories(
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                default_priority TEXT NOT NULL,
                description TEXT
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickets(
                ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT DEFAULT 'Open',
                location TEXT NOT NULL,
                created_by INTEGER NOT NULL,
                assigned_to INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                resolved_at TEXT,
                closed_at TEXT,
                estimated_completion TEXT,
                resolution_details TEXT,
                FOREIGN KEY(created_by) REFERENCES users(user_id),
                FOREIGN KEY(assigned_to) REFERENCES users(user_id)
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments(
                comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                comment_type TEXT DEFAULT 'public',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(ticket_id) REFERENCES tickets(ticket_id),
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS attachments(
                attachment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                filedata BLOB NOT NULL,
                filesize INTEGER NOT NULL,
                filetype TEXT NOT NULL,
                uploaded_by INTEGER NOT NULL,
                uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(ticket_id) REFERENCES tickets(ticket_id),
                FOREIGN KEY(uploaded_by) REFERENCES users(user_id)
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ticket_history(
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(ticket_id) REFERENCES tickets(ticket_id),
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS escalation_rules(
                rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                priority TEXT NOT NULL,
                time_limit_hours INTEGER NOT NULL,
                description TEXT
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS technician_limits(
                limit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                technician_id INTEGER NOT NULL,
                max_open_tickets INTEGER DEFAULT 20,
                FOREIGN KEY(technician_id) REFERENCES users(user_id)
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications(
                notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                ticket_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                read_status TEXT DEFAULT 'unread',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id),
                FOREIGN KEY(ticket_id) REFERENCES tickets(ticket_id)
            )
        """)
        
        self.conn.commit()
    
    def insert_default_data(self):
        self.cursor.execute("SELECT COUNT(*) FROM users")
        if self.cursor.fetchone()[0] == 0:
            default_users = [
                ('Admin User', 'admin@university.edu', self.hash_password('admin123'), 'Administrator'),
                ('John Technician', 'john.tech@university.edu', self.hash_password('tech123'), 'Technician'),
                ('Sarah Tech', 'sarah.tech@university.edu', self.hash_password('tech123'), 'Technician'),
                ('Student One', 'student1@university.edu', self.hash_password('student123'), 'Student'),
                ('Faculty Member', 'faculty1@university.edu', self.hash_password('faculty123'), 'Faculty'),
                ('Staff Member', 'staff1@university.edu', self.hash_password('staff123'), 'Staff')
            ]
            self.cursor.executemany("INSERT INTO users(name, email, password, role) VALUES(?,?,?,?)", default_users)
        
        self.cursor.execute("SELECT COUNT(*) FROM ticket_categories")
        if self.cursor.fetchone()[0] == 0:
            categories = [
                ('Network', 'High', 'Network connectivity and internet issues'),
                ('Hardware', 'Medium', 'Computer hardware and peripherals'),
                ('Software', 'Low', 'Software installation and application issues'),
                ('Account Access', 'High', 'Login and account access problems'),
                ('Email', 'Medium', 'Email service issues'),
                ('Printing', 'Low', 'Printer and printing problems'),
                ('Security', 'High', 'Security and cybersecurity concerns'),
                ('Other', 'Low', 'Other IT related issues')
            ]
            self.cursor.executemany("INSERT INTO ticket_categories(name, default_priority, description) VALUES(?,?,?)", categories)
        
        self.cursor.execute("SELECT COUNT(*) FROM escalation_rules")
        if self.cursor.fetchone()[0] == 0:
            rules = [
                ('High', 4, 'High priority tickets must be addressed within 4 hours'),
                ('Medium', 24, 'Medium priority tickets must be addressed within 24 hours'),
                ('Low', 72, 'Low priority tickets must be addressed within 72 hours')
            ]
            self.cursor.executemany("INSERT INTO escalation_rules(priority, time_limit_hours, description) VALUES(?,?,?)", rules)
        
        self.conn.commit()
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate_user(self, email, password):
        hashed_password = self.hash_password(password)
        self.cursor.execute("SELECT user_id, name, email, role, status FROM users WHERE email=? AND password=?", 
                           (email, hashed_password))
        user = self.cursor.fetchone()
        if user and user[4] == 'active':
            return {'user_id': user[0], 'name': user[1], 'email': user[2], 'role': user[3]}
        return None
    
    def create_user(self, name, email, password, role):
        try:
            hashed_password = self.hash_password(password)
            self.cursor.execute("INSERT INTO users(name, email, password, role) VALUES(?,?,?,?)", 
                              (name, email, hashed_password, role))
            self.conn.commit()
            return True
        except:
            return False
    
    def get_categories(self):
        self.cursor.execute("SELECT name, default_priority FROM ticket_categories ORDER BY name")
        return self.cursor.fetchall()
    
    def get_priority_for_category(self, category):
        self.cursor.execute("SELECT default_priority FROM ticket_categories WHERE name=?", (category,))
        result = self.cursor.fetchone()
        return result[0] if result else 'Low'
    
    def create_ticket(self, title, description, category, location, created_by):
        priority = self.get_priority_for_category(category)
        self.cursor.execute("""
            INSERT INTO tickets(title, description, category, priority, status, location, created_by)
            VALUES(?,?,?,?,?,?,?)
        """, (title, description, category, priority, 'Open', location, created_by))
        ticket_id = self.cursor.lastrowid
        
        self.cursor.execute("""
            INSERT INTO ticket_history(ticket_id, user_id, action, new_value)
            VALUES(?,?,?,?)
        """, (ticket_id, created_by, 'Created', f'Ticket created with priority {priority}'))
        
        self.conn.commit()
        return ticket_id
    
    def get_user_tickets(self, user_id):
        self.cursor.execute("""
            SELECT t.ticket_id, t.title, t.category, t.priority, t.status, t.created_at, 
                   u.name as assigned_to_name
            FROM tickets t
            LEFT JOIN users u ON t.assigned_to = u.user_id
            WHERE t.created_by = ?
            ORDER BY t.created_at DESC
        """, (user_id,))
        return self.cursor.fetchall()
    
    def get_ticket_details(self, ticket_id):
        self.cursor.execute("""
            SELECT t.*, u1.name as creator_name, u2.name as assigned_name, u2.email as assigned_email
            FROM tickets t
            LEFT JOIN users u1 ON t.created_by = u1.user_id
            LEFT JOIN users u2 ON t.assigned_to = u2.user_id
            WHERE t.ticket_id = ?
        """, (ticket_id,))
        return self.cursor.fetchone()
    
    def get_ticket_comments(self, ticket_id):
        self.cursor.execute("""
            SELECT c.comment_id, c.message, c.comment_type, c.created_at, u.name, u.role
            FROM comments c
            JOIN users u ON c.user_id = u.user_id
            WHERE c.ticket_id = ?
            ORDER BY c.created_at ASC
        """, (ticket_id,))
        return self.cursor.fetchall()
    
    def add_comment(self, ticket_id, user_id, message, comment_type='public'):
        self.cursor.execute("""
            INSERT INTO comments(ticket_id, user_id, message, comment_type)
            VALUES(?,?,?,?)
        """, (ticket_id, user_id, message, comment_type))
        
        self.cursor.execute("UPDATE tickets SET updated_at = CURRENT_TIMESTAMP WHERE ticket_id = ?", (ticket_id,))
        
        self.cursor.execute("""
            INSERT INTO ticket_history(ticket_id, user_id, action, new_value)
            VALUES(?,?,?,?)
        """, (ticket_id, user_id, 'Comment Added', f'{comment_type.capitalize()} comment added'))
        
        self.conn.commit()
    
    def update_ticket_status(self, ticket_id, status, user_id):
        if status == 'Resolved':
            self.cursor.execute("""
                UPDATE tickets SET status=?, resolved_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP
                WHERE ticket_id=?
            """, (status, ticket_id))
        elif status == 'Closed':
            self.cursor.execute("""
                UPDATE tickets SET status=?, closed_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP
                WHERE ticket_id=?
            """, (status, ticket_id))
        else:
            self.cursor.execute("""
                UPDATE tickets SET status=?, updated_at=CURRENT_TIMESTAMP WHERE ticket_id=?
            """, (status, ticket_id))
        
        self.cursor.execute("""
            INSERT INTO ticket_history(ticket_id, user_id, action, new_value)
            VALUES(?,?,?,?)
        """, (ticket_id, user_id, 'Status Changed', f'Status changed to {status}'))
        
        self.conn.commit()
    
    def assign_ticket(self, ticket_id, technician_id, assigned_by):
        self.cursor.execute("""
            UPDATE tickets SET assigned_to=?, status='In Progress', updated_at=CURRENT_TIMESTAMP
            WHERE ticket_id=?
        """, (technician_id, ticket_id))
        
        self.cursor.execute("""
            INSERT INTO ticket_history(ticket_id, user_id, action, new_value)
            VALUES(?,?,?,?)
        """, (ticket_id, assigned_by, 'Assigned', f'Ticket assigned to technician ID {technician_id}'))
        
        self.conn.commit()
    
    def get_unassigned_tickets(self):
        self.cursor.execute("""
            SELECT t.ticket_id, t.title, t.category, t.priority, t.status, t.created_at,
                   u.name as creator_name, t.location
            FROM tickets t
            JOIN users u ON t.created_by = u.user_id
            WHERE t.assigned_to IS NULL AND t.status != 'Cancelled' AND t.status != 'Closed'
            ORDER BY 
                CASE t.priority 
                    WHEN 'High' THEN 1 
                    WHEN 'Medium' THEN 2 
                    ELSE 3 
                END,
                t.created_at ASC
        """)
        return self.cursor.fetchall()
    
    def get_technician_tickets(self, technician_id):
        self.cursor.execute("""
            SELECT t.ticket_id, t.title, t.category, t.priority, t.status, t.created_at,
                   u.name as creator_name, t.location
            FROM tickets t
            JOIN users u ON t.created_by = u.user_id
            WHERE t.assigned_to = ? AND t.status != 'Closed'
            ORDER BY 
                CASE t.priority 
                    WHEN 'High' THEN 1 
                    WHEN 'Medium' THEN 2 
                    ELSE 3 
                END,
                t.created_at ASC
        """, (technician_id,))
        return self.cursor.fetchall()
    
    def search_tickets(self, search_term, user_id, role):
        search_pattern = f'%{search_term}%'
        if role in ['Student', 'Faculty', 'Staff']:
            self.cursor.execute("""
                SELECT t.ticket_id, t.title, t.category, t.priority, t.status, t.created_at
                FROM tickets t
                WHERE t.created_by = ? AND (
                    t.title LIKE ? OR 
                    t.description LIKE ? OR 
                    t.category LIKE ? OR
                    CAST(t.ticket_id AS TEXT) = ?
                )
                ORDER BY t.created_at DESC
            """, (user_id, search_pattern, search_pattern, search_pattern, search_term))
        else:
            self.cursor.execute("""
                SELECT t.ticket_id, t.title, t.category, t.priority, t.status, t.created_at
                FROM tickets t
                WHERE t.title LIKE ? OR 
                      t.description LIKE ? OR 
                      t.category LIKE ? OR
                      CAST(t.ticket_id AS TEXT) = ?
                ORDER BY t.created_at DESC
            """, (search_pattern, search_pattern, search_pattern, search_term))
        return self.cursor.fetchall()
    
    def can_reopen_ticket(self, ticket_id):
        self.cursor.execute("""
            SELECT resolved_at FROM tickets WHERE ticket_id = ? AND status = 'Resolved'
        """, (ticket_id,))
        result = self.cursor.fetchone()
        if result and result[0]:
            resolved_time = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
            days_passed = (datetime.now() - resolved_time).days
            return days_passed <= 5
        return False
    
    def can_cancel_ticket(self, ticket_id):
        self.cursor.execute("""
            SELECT status FROM tickets WHERE ticket_id = ?
        """, (ticket_id,))
        result = self.cursor.fetchone()
        return result and result[0] == 'Open'
    
    def upload_attachment(self, ticket_id, filename, filedata, filesize, filetype, uploaded_by):
        if filesize > 10485760:
            return False
        try:
            self.cursor.execute("""
                INSERT INTO attachments(ticket_id, filename, filedata, filesize, filetype, uploaded_by)
                VALUES(?,?,?,?,?,?)
            """, (ticket_id, filename, filedata, filesize, filetype, uploaded_by))
            
            self.cursor.execute("""
                INSERT INTO ticket_history(ticket_id, user_id, action, new_value)
                VALUES(?,?,?,?)
            """, (ticket_id, uploaded_by, 'Attachment Added', f'File: {filename}'))
            
            self.conn.commit()
            return True
        except:
            return False
    
    def get_attachments(self, ticket_id):
        self.cursor.execute("""
            SELECT attachment_id, filename, filesize, filetype, uploaded_at, u.name
            FROM attachments a
            JOIN users u ON a.uploaded_by = u.user_id
            WHERE ticket_id = ?
            ORDER BY uploaded_at DESC
        """, (ticket_id,))
        return self.cursor.fetchall()
    
    def get_attachment_data(self, attachment_id):
        self.cursor.execute("""
            SELECT filename, filedata, filetype FROM attachments WHERE attachment_id = ?
        """, (attachment_id,))
        return self.cursor.fetchone()
    
    def get_all_tickets_for_admin(self):
        self.cursor.execute("""
            SELECT t.ticket_id, t.title, t.category, t.priority, t.status, t.created_at,
                   u1.name as creator_name, u2.name as assigned_name
            FROM tickets t
            JOIN users u1 ON t.created_by = u1.user_id
            LEFT JOIN users u2 ON t.assigned_to = u2.user_id
            ORDER BY t.created_at DESC
        """)
        return self.cursor.fetchall()
    
    def get_all_technicians(self):
        self.cursor.execute("""
            SELECT user_id, name, email, status FROM users WHERE role = 'Technician'
            ORDER BY name
        """)
        return self.cursor.fetchall()
    
    def deactivate_user(self, user_id):
        self.cursor.execute("UPDATE users SET status = 'inactive' WHERE user_id = ?", (user_id,))
        self.conn.commit()
    
    def activate_user(self, user_id):
        self.cursor.execute("UPDATE users SET status = 'active' WHERE user_id = ?", (user_id,))
        self.conn.commit()
    
    def get_ticket_stats(self):
        stats = {}
        
        self.cursor.execute("SELECT COUNT(*) FROM tickets")
        stats['total'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'Open'")
        stats['open'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'In Progress'")
        stats['in_progress'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'Resolved'")
        stats['resolved'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'Closed'")
        stats['closed'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'Cancelled'")
        stats['cancelled'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'Pending'")
        stats['pending'] = self.cursor.fetchone()[0]
        
        return stats
    
    def get_category_stats(self):
        self.cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM tickets
            GROUP BY category
            ORDER BY count DESC
        """)
        return self.cursor.fetchall()
    
    def get_priority_stats(self):
        self.cursor.execute("""
            SELECT priority, COUNT(*) as count
            FROM tickets
            GROUP BY priority
            ORDER BY 
                CASE priority 
                    WHEN 'High' THEN 1 
                    WHEN 'Medium' THEN 2 
                    ELSE 3 
                END
        """)
        return self.cursor.fetchall()
    
    def get_average_resolution_time(self):
        self.cursor.execute("""
            SELECT AVG(
                CAST((julianday(resolved_at) - julianday(created_at)) * 24 AS INTEGER)
            ) as avg_hours
            FROM tickets
            WHERE resolved_at IS NOT NULL
        """)
        result = self.cursor.fetchone()
        return result[0] if result[0] else 0
    
    def get_technician_performance(self):
        self.cursor.execute("""
            SELECT u.name, 
                   COUNT(CASE WHEN t.status = 'Closed' THEN 1 END) as closed_tickets,
                   COUNT(CASE WHEN t.status = 'In Progress' THEN 1 END) as active_tickets,
                   AVG(CASE WHEN t.resolved_at IS NOT NULL 
                       THEN CAST((julianday(t.resolved_at) - julianday(t.created_at)) * 24 AS INTEGER)
                       END) as avg_resolution_hours
            FROM users u
            LEFT JOIN tickets t ON u.user_id = t.assigned_to
            WHERE u.role = 'Technician'
            GROUP BY u.user_id, u.name
            ORDER BY closed_tickets DESC
        """)
        return self.cursor.fetchall()
    
    def get_overdue_tickets(self):
        self.cursor.execute("""
            SELECT t.ticket_id, t.title, t.priority, t.created_at, t.status,
                   er.time_limit_hours,
                   CAST((julianday('now') - julianday(t.created_at)) * 24 AS INTEGER) as hours_elapsed
            FROM tickets t
            JOIN escalation_rules er ON t.priority = er.priority
            WHERE t.status NOT IN ('Closed', 'Resolved', 'Cancelled')
              AND CAST((julianday('now') - julianday(t.created_at)) * 24 AS INTEGER) > er.time_limit_hours
            ORDER BY hours_elapsed DESC
        """)
        return self.cursor.fetchall()
    
    def update_ticket_priority(self, ticket_id, priority, user_id):
        self.cursor.execute("""
            UPDATE tickets SET priority = ?, updated_at = CURRENT_TIMESTAMP WHERE ticket_id = ?
        """, (priority, ticket_id))
        
        self.cursor.execute("""
            INSERT INTO ticket_history(ticket_id, user_id, action, new_value)
            VALUES(?,?,?,?)
        """, (ticket_id, user_id, 'Priority Changed', f'Priority changed to {priority}'))
        
        self.conn.commit()
    
    def set_estimated_completion(self, ticket_id, estimated_time, user_id):
        self.cursor.execute("""
            UPDATE tickets SET estimated_completion = ?, updated_at = CURRENT_TIMESTAMP
            WHERE ticket_id = ?
        """, (estimated_time, ticket_id))
        
        self.cursor.execute("""
            INSERT INTO ticket_history(ticket_id, user_id, action, new_value)
            VALUES(?,?,?,?)
        """, (ticket_id, user_id, 'Estimated Completion Set', estimated_time))
        
        self.conn.commit()
    
    def close_ticket_with_resolution(self, ticket_id, resolution_details, user_id):
        self.cursor.execute("""
            UPDATE tickets 
            SET status = 'Closed', 
                resolution_details = ?,
                closed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE ticket_id = ?
        """, (resolution_details, ticket_id))
        
        self.cursor.execute("""
            INSERT INTO ticket_history(ticket_id, user_id, action, new_value)
            VALUES(?,?,?,?)
        """, (ticket_id, user_id, 'Ticket Closed', 'Ticket closed with resolution'))
        
        self.conn.commit()
    
    def get_ticket_history(self, ticket_id):
        self.cursor.execute("""
            SELECT h.action, h.old_value, h.new_value, h.created_at, u.name
            FROM ticket_history h
            JOIN users u ON h.user_id = u.user_id
            WHERE h.ticket_id = ?
            ORDER BY h.created_at DESC
        """, (ticket_id,))
        return self.cursor.fetchall()
    
    def reassign_ticket(self, ticket_id, new_technician_id, user_id):
        self.cursor.execute("""
            UPDATE tickets SET assigned_to = ?, updated_at = CURRENT_TIMESTAMP
            WHERE ticket_id = ?
        """, (new_technician_id, ticket_id))
        
        self.cursor.execute("""
            INSERT INTO ticket_history(ticket_id, user_id, action, new_value)
            VALUES(?,?,?,?)
        """, (ticket_id, user_id, 'Reassigned', f'Ticket reassigned to technician ID {new_technician_id}'))
        
        self.conn.commit()
    
    def get_technician_workload(self, technician_id):
        self.cursor.execute("""
            SELECT COUNT(*) FROM tickets 
            WHERE assigned_to = ? AND status NOT IN ('Closed', 'Cancelled')
        """, (technician_id,))
        return self.cursor.fetchone()[0]
    
    def add_category(self, name, priority, description):
        try:
            self.cursor.execute("""
                INSERT INTO ticket_categories(name, default_priority, description)
                VALUES(?,?,?)
            """, (name, priority, description))
            self.conn.commit()
            return True
        except:
            return False
    
    def update_escalation_rule(self, priority, hours):
        self.cursor.execute("""
            UPDATE escalation_rules SET time_limit_hours = ? WHERE priority = ?
        """, (hours, priority))
        self.conn.commit()
    
    def set_technician_limit(self, technician_id, max_tickets):
        self.cursor.execute("""
            INSERT OR REPLACE INTO technician_limits(technician_id, max_open_tickets)
            VALUES(?,?)
        """, (technician_id, max_tickets))
        self.conn.commit()
    
    def archive_old_tickets(self, days=90):
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        self.cursor.execute("""
            UPDATE tickets SET status = 'Archived'
            WHERE status = 'Closed' AND closed_at < ?
        """, (cutoff_date,))
        self.conn.commit()
        return self.cursor.rowcount

def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'db' not in st.session_state:
        st.session_state.db = Database()

def login_page():
    st.title("Campus IT Helpdesk System")
    st.subheader("Login")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            user = st.session_state.db.authenticate_user(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.success(f"Welcome {user['name']}!")
                st.rerun()
            else:
                st.error("Invalid credentials or inactive account")
    
    with tab2:
        st.subheader("Register New Account")
        reg_name = st.text_input("Full Name", key="reg_name")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_role = st.selectbox("Role", ["Student", "Faculty", "Staff"])
        
        if st.button("Register"):
            if reg_name and reg_email and reg_password:
                if st.session_state.db.create_user(reg_name, reg_email, reg_password, reg_role):
                    st.success("Account created successfully! Please login.")
                else:
                    st.error("Email already exists")
            else:
                st.error("All fields are required")

def student_dashboard():
    st.title("My IT Support Tickets")
    
    menu = st.sidebar.selectbox("Menu", [
        "Submit New Ticket",
        "My Tickets",
        "Search Tickets"
    ])
    
    if menu == "Submit New Ticket":
        submit_ticket_form()
    elif menu == "My Tickets":
        view_my_tickets()
    elif menu == "Search Tickets":
        search_tickets_page()

def submit_ticket_form():
    st.subheader("Submit New IT Support Ticket")
    
    categories = st.session_state.db.get_categories()
    category_names = [cat[0] for cat in categories]
    
    with st.form("submit_ticket"):
        title = st.text_input("Issue Title")
        description = st.text_area("Detailed Description")
        category = st.selectbox("Category", category_names)
        location = st.text_input("Location")
        
        uploaded_file = st.file_uploader("Attach File (Optional, Max 10MB)", 
                                        type=['png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx', 'txt'])
        
        submitted = st.form_submit_button("Submit Ticket")
        
        if submitted:
            if title and description and category and location:
                ticket_id = st.session_state.db.create_ticket(
                    title, description, category, location, 
                    st.session_state.user['user_id']
                )
                
                if uploaded_file:
                    filedata = uploaded_file.read()
                    filesize = len(filedata)
                    if st.session_state.db.upload_attachment(
                        ticket_id, uploaded_file.name, filedata, 
                        filesize, uploaded_file.type,
                        st.session_state.user['user_id']
                    ):
                        st.success(f"Ticket #{ticket_id} submitted with attachment!")
                    else:
                        st.warning(f"Ticket #{ticket_id} submitted but attachment failed (file too large)")
                else:
                    st.success(f"Ticket #{ticket_id} submitted successfully!")
            else:
                st.error("All fields are required")

def view_my_tickets():
    st.subheader("My Tickets")
    
    tickets = st.session_state.db.get_user_tickets(st.session_state.user['user_id'])
    
    if tickets:
        df = pd.DataFrame(tickets, columns=[
            'ID', 'Title', 'Category', 'Priority', 'Status', 'Created', 'Assigned To'
        ])
        
        st.dataframe(df, use_container_width=True)
        
        ticket_id = st.selectbox("Select Ticket to View Details", [t[0] for t in tickets])
        
        if ticket_id:
            show_ticket_details(ticket_id, is_creator=True)
    else:
        st.info("No tickets found")

def show_ticket_details(ticket_id, is_creator=False, is_technician=False, is_admin=False):
    ticket = st.session_state.db.get_ticket_details(ticket_id)
    
    if not ticket:
        st.error("Ticket not found")
        return
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Ticket ID", f"#{ticket[0]}")
        st.metric("Priority", ticket[4])
    with col2:
        st.metric("Status", ticket[5])
        st.metric("Category", ticket[3])
    with col3:
        st.metric("Location", ticket[6])
        if ticket[13]:
            st.metric("Assigned To", ticket[13])
    
    st.write(f"**Title:** {ticket[1]}")
    st.write(f"**Description:** {ticket[2]}")
    st.write(f"**Created:** {ticket[8]}")
    st.write(f"**Created By:** {ticket[12]}")
    
    if ticket[10]:
        st.write(f"**Estimated Completion:** {ticket[10]}")
    if ticket[11]:
        st.write(f"**Resolution Details:** {ticket[11]}")
    
    attachments = st.session_state.db.get_attachments(ticket_id)
    if attachments:
        st.subheader("Attachments")
        for att in attachments:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"{att[1]} ({att[2]} bytes)")
            with col2:
                st.write(f"Uploaded by {att[5]} on {att[4]}")
            with col3:
                if st.button("Download", key=f"dl_{att[0]}"):
                    data = st.session_state.db.get_attachment_data(att[0])
                    if data:
                        st.download_button(
                            "Click to download",
                            data[1],
                            file_name=data[0],
                            mime=data[2],
                            key=f"dld_{att[0]}"
                        )
    
    if is_creator or is_technician or is_admin:
        st.subheader("Add Comment")
        comment_text = st.text_area("Your Comment", key=f"comment_{ticket_id}")
        
        if is_technician or is_admin:
            comment_type = st.radio("Comment Type", ["public", "internal"], key=f"type_{ticket_id}")
        else:
            comment_type = "public"
        
        if st.button("Add Comment", key=f"btn_comment_{ticket_id}"):
            if comment_text:
                st.session_state.db.add_comment(
                    ticket_id, st.session_state.user['user_id'], 
                    comment_text, comment_type
                )
                st.success("Comment added")
                st.rerun()
        
        uploaded_file = st.file_uploader("Add Attachment", key=f"attach_{ticket_id}",
                                        type=['png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx', 'txt'])
        if uploaded_file and st.button("Upload", key=f"upload_{ticket_id}"):
            filedata = uploaded_file.read()
            filesize = len(filedata)
            if st.session_state.db.upload_attachment(
                ticket_id, uploaded_file.name, filedata, 
                filesize, uploaded_file.type,
                st.session_state.user['user_id']
            ):
                st.success("Attachment uploaded")
                st.rerun()
            else:
                st.error("Upload failed (file too large)")
    
    st.subheader("Comments and Updates")
    comments = st.session_state.db.get_ticket_comments(ticket_id)
    
    for comment in comments:
        if comment[2] == 'internal' and not (is_technician or is_admin):
            continue
        
        with st.container():
            st.write(f"**{comment[4]}** ({comment[5]}) - {comment[3]}")
            if comment[2] == 'internal':
                st.caption("Internal Note")
            st.write(comment[1])
            st.divider()
    
    if is_creator:
        col1, col2 = st.columns(2)
        with col1:
            if ticket[5] == 'Resolved' and st.session_state.db.can_reopen_ticket(ticket_id):
                if st.button("Reopen Ticket", key=f"reopen_{ticket_id}"):
                    st.session_state.db.update_ticket_status(
                        ticket_id, 'Open', st.session_state.user['user_id']
                    )
                    st.success("Ticket reopened")
                    st.rerun()
        
        with col2:
            if st.session_state.db.can_cancel_ticket(ticket_id):
                if st.button("Cancel Ticket", key=f"cancel_{ticket_id}"):
                    st.session_state.db.update_ticket_status(
                        ticket_id, 'Cancelled', st.session_state.user['user_id']
                    )
                    st.success("Ticket cancelled")
                    st.rerun()
    
    if is_technician or is_admin:
        st.subheader("Technician Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_status = st.selectbox(
                "Update Status",
                ['Open', 'In Progress', 'Pending', 'Resolved', 'Closed'],
                key=f"status_{ticket_id}"
            )
            if st.button("Update Status", key=f"btn_status_{ticket_id}"):
                st.session_state.db.update_ticket_status(
                    ticket_id, new_status, st.session_state.user['user_id']
                )
                st.success("Status updated")
                st.rerun()
        
        with col2:
            new_priority = st.selectbox(
                "Update Priority",
                ['High', 'Medium', 'Low'],
                key=f"priority_{ticket_id}"
            )
            if st.button("Update Priority", key=f"btn_priority_{ticket_id}"):
                st.session_state.db.update_ticket_priority(
                    ticket_id, new_priority, st.session_state.user['user_id']
                )
                st.success("Priority updated")
                st.rerun()
        
        with col3:
            est_time = st.text_input("Est. Completion", key=f"est_{ticket_id}")
            if st.button("Set Estimate", key=f"btn_est_{ticket_id}"):
                if est_time:
                    st.session_state.db.set_estimated_completion(
                        ticket_id, est_time, st.session_state.user['user_id']
                    )
                    st.success("Estimate set")
                    st.rerun()
        
        if ticket[7]:
            technicians = st.session_state.db.get_all_technicians()
            tech_options = {t[1]: t[0] for t in technicians if t[3] == 'active'}
            
            selected_tech = st.selectbox(
                "Reassign To",
                list(tech_options.keys()),
                key=f"reassign_{ticket_id}"
            )
            if st.button("Reassign", key=f"btn_reassign_{ticket_id}"):
                st.session_state.db.reassign_ticket(
                    ticket_id, tech_options[selected_tech], 
                    st.session_state.user['user_id']
                )
                st.success("Ticket reassigned")
                st.rerun()
        
        if ticket[5] not in ['Closed']:
            resolution_text = st.text_area("Resolution Details", key=f"res_{ticket_id}")
            if st.button("Close with Resolution", key=f"btn_close_{ticket_id}"):
                if resolution_text:
                    st.session_state.db.close_ticket_with_resolution(
                        ticket_id, resolution_text, st.session_state.user['user_id']
                    )
                    st.success("Ticket closed")
                    st.rerun()
                else:
                    st.error("Resolution details required")
    
    with st.expander("View History"):
        history = st.session_state.db.get_ticket_history(ticket_id)
        for h in history:
            st.write(f"**{h[4]}** - {h[0]} - {h[3]}")
            if h[2]:
                st.caption(h[2])

def search_tickets_page():
    st.subheader("Search Tickets")
    
    search_term = st.text_input("Enter Ticket ID or Keyword")
    
    if st.button("Search"):
        if search_term:
            results = st.session_state.db.search_tickets(
                search_term, 
                st.session_state.user['user_id'],
                st.session_state.user['role']
            )
            
            if results:
                df = pd.DataFrame(results, columns=[
                    'ID', 'Title', 'Category', 'Priority', 'Status', 'Created'
                ])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No tickets found")

def technician_dashboard():
    st.title("Technician Dashboard")
    
    menu = st.sidebar.selectbox("Menu", [
        "My Assigned Tickets",
        "Unassigned Tickets",
        "Search All Tickets",
        "My Workload"
    ])
    
    if menu == "My Assigned Tickets":
        view_assigned_tickets()
    elif menu == "Unassigned Tickets":
        view_unassigned_tickets()
    elif menu == "Search All Tickets":
        search_all_tickets()
    elif menu == "My Workload":
        view_workload()

def view_assigned_tickets():
    st.subheader("My Assigned Tickets")
    
    tickets = st.session_state.db.get_technician_tickets(st.session_state.user['user_id'])
    
    if tickets:
        df = pd.DataFrame(tickets, columns=[
            'ID', 'Title', 'Category', 'Priority', 'Status', 'Created', 'Creator', 'Location'
        ])
        
        st.dataframe(df, use_container_width=True)
        
        ticket_id = st.selectbox("Select Ticket", [t[0] for t in tickets])
        
        if ticket_id:
            show_ticket_details(ticket_id, is_technician=True)
    else:
        st.info("No assigned tickets")

def view_unassigned_tickets():
    st.subheader("Unassigned Tickets")
    
    tickets = st.session_state.db.get_unassigned_tickets()
    
    if tickets:
        df = pd.DataFrame(tickets, columns=[
            'ID', 'Title', 'Category', 'Priority', 'Status', 'Created', 'Creator', 'Location'
        ])
        
        st.dataframe(df, use_container_width=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            ticket_id = st.selectbox("Select Ticket to View/Accept", [t[0] for t in tickets])
        with col2:
            st.write("")
            st.write("")
            if st.button("Accept Ticket"):
                st.session_state.db.assign_ticket(
                    ticket_id, 
                    st.session_state.user['user_id'],
                    st.session_state.user['user_id']
                )
                st.success("Ticket accepted")
                st.rerun()
        
        if ticket_id:
            show_ticket_details(ticket_id, is_technician=True)
    else:
        st.info("No unassigned tickets")

def search_all_tickets():
    st.subheader("Search All Tickets")
    
    search_term = st.text_input("Enter Ticket ID or Keyword")
    
    if st.button("Search"):
        if search_term:
            results = st.session_state.db.search_tickets(
                search_term,
                st.session_state.user['user_id'],
                st.session_state.user['role']
            )
            
            if results:
                df = pd.DataFrame(results, columns=[
                    'ID', 'Title', 'Category', 'Priority', 'Status', 'Created'
                ])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No tickets found")

def view_workload():
    st.subheader("My Workload")
    
    workload = st.session_state.db.get_technician_workload(st.session_state.user['user_id'])
    
    st.metric("Active Tickets", workload)
    
    tickets = st.session_state.db.get_technician_tickets(st.session_state.user['user_id'])
    
    if tickets:
        by_priority = {}
        by_status = {}
        
        for ticket in tickets:
            priority = ticket[3]
            status = ticket[4]
            
            by_priority[priority] = by_priority.get(priority, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**By Priority:**")
            for priority, count in by_priority.items():
                st.write(f"{priority}: {count}")
        
        with col2:
            st.write("**By Status:**")
            for status, count in by_status.items():
                st.write(f"{status}: {count}")

def admin_dashboard():
    st.title("Administrator Dashboard")
    
    menu = st.sidebar.selectbox("Menu", [
        "Dashboard Overview",
        "All Tickets",
        "Manage Users",
        "Manage Categories",
        "Reports",
        "System Settings"
    ])
    
    if menu == "Dashboard Overview":
        dashboard_overview()
    elif menu == "All Tickets":
        view_all_tickets()
    elif menu == "Manage Users":
        manage_users()
    elif menu == "Manage Categories":
        manage_categories()
    elif menu == "Reports":
        generate_reports()
    elif menu == "System Settings":
        system_settings()

def dashboard_overview():
    st.subheader("System Overview")
    
    stats = st.session_state.db.get_ticket_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tickets", stats['total'])
        st.metric("Open", stats['open'])
    with col2:
        st.metric("In Progress", stats['in_progress'])
        st.metric("Pending", stats['pending'])
    with col3:
        st.metric("Resolved", stats['resolved'])
        st.metric("Closed", stats['closed'])
    with col4:
        st.metric("Cancelled", stats['cancelled'])
        avg_time = st.session_state.db.get_average_resolution_time()
        st.metric("Avg Resolution (hrs)", f"{avg_time:.1f}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Tickets by Category")
        cat_stats = st.session_state.db.get_category_stats()
        if cat_stats:
            df = pd.DataFrame(cat_stats, columns=['Category', 'Count'])
            fig = px.pie(df, values='Count', names='Category', title='Tickets by Category')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Tickets by Priority")
        pri_stats = st.session_state.db.get_priority_stats()
        if pri_stats:
            df = pd.DataFrame(pri_stats, columns=['Priority', 'Count'])
            fig = px.bar(df, x='Priority', y='Count', title='Tickets by Priority')
            st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Overdue Tickets")
    overdue = st.session_state.db.get_overdue_tickets()
    if overdue:
        df = pd.DataFrame(overdue, columns=[
            'ID', 'Title', 'Priority', 'Created', 'Status', 
            'Time Limit (hrs)', 'Hours Elapsed'
        ])
        st.dataframe(df, use_container_width=True)
    else:
        st.success("No overdue tickets")

def view_all_tickets():
    st.subheader("All Tickets")
    
    tickets = st.session_state.db.get_all_tickets_for_admin()
    
    if tickets:
        df = pd.DataFrame(tickets, columns=[
            'ID', 'Title', 'Category', 'Priority', 'Status', 
            'Created', 'Creator', 'Assigned To'
        ])
        
        st.dataframe(df, use_container_width=True)
        
        ticket_id = st.selectbox("Select Ticket", [t[0] for t in tickets])
        
        if ticket_id:
            show_ticket_details(ticket_id, is_admin=True)
    else:
        st.info("No tickets found")

def manage_users():
    st.subheader("Manage Users")
    
    tab1, tab2 = st.tabs(["Create User", "Manage Technicians"])
    
    with tab1:
        st.write("**Create New Technician Account**")
        
        with st.form("create_tech"):
            name = st.text_input("Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            
            submitted = st.form_submit_button("Create Account")
            
            if submitted:
                if name and email and password:
                    if st.session_state.db.create_user(name, email, password, "Technician"):
                        st.success("Technician account created")
                    else:
                        st.error("Email already exists")
                else:
                    st.error("All fields required")
    
    with tab2:
        st.write("**Active Technicians**")
        
        technicians = st.session_state.db.get_all_technicians()
        
        if technicians:
            for tech in technicians:
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                
                with col1:
                    st.write(tech[1])
                with col2:
                    st.write(tech[2])
                with col3:
                    st.write(tech[3])
                with col4:
                    if tech[3] == 'active':
                        if st.button("Deactivate", key=f"deact_{tech[0]}"):
                            st.session_state.db.deactivate_user(tech[0])
                            st.rerun()
                    else:
                        if st.button("Activate", key=f"act_{tech[0]}"):
                            st.session_state.db.activate_user(tech[0])
                            st.rerun()

def manage_categories():
    st.subheader("Manage Categories")
    
    categories = st.session_state.db.get_categories()
    
    st.write("**Existing Categories**")
    df = pd.DataFrame(categories, columns=['Category', 'Default Priority'])
    st.dataframe(df, use_container_width=True)
    
    st.write("**Add New Category**")
    
    with st.form("add_category"):
        name = st.text_input("Category Name")
        priority = st.selectbox("Default Priority", ['High', 'Medium', 'Low'])
        description = st.text_area("Description")
        
        submitted = st.form_submit_button("Add Category")
        
        if submitted:
            if name:
                if st.session_state.db.add_category(name, priority, description):
                    st.success("Category added")
                    st.rerun()
                else:
                    st.error("Category already exists")

def generate_reports():
    st.subheader("Reports and Analytics")
    
    report_type = st.selectbox("Select Report Type", [
        "Ticket Volume by Category",
        "Technician Performance",
        "Average Resolution Time",
        "Overdue Tickets",
        "Status Distribution"
    ])
    
    if report_type == "Ticket Volume by Category":
        cat_stats = st.session_state.db.get_category_stats()
        if cat_stats:
            df = pd.DataFrame(cat_stats, columns=['Category', 'Count'])
            st.dataframe(df, use_container_width=True)
            
            fig = px.bar(df, x='Category', y='Count', title='Ticket Volume by Category')
            st.plotly_chart(fig, use_container_width=True)
            
            csv = df.to_csv(index=False)
            st.download_button("Download CSV", csv, "category_report.csv", "text/csv")
    
    elif report_type == "Technician Performance":
        perf = st.session_state.db.get_technician_performance()
        if perf:
            df = pd.DataFrame(perf, columns=[
                'Technician', 'Closed Tickets', 'Active Tickets', 'Avg Resolution (hrs)'
            ])
            st.dataframe(df, use_container_width=True)
            
            fig = px.bar(df, x='Technician', y='Closed Tickets', 
                        title='Technician Performance - Closed Tickets')
            st.plotly_chart(fig, use_container_width=True)
            
            csv = df.to_csv(index=False)
            st.download_button("Download CSV", csv, "technician_report.csv", "text/csv")
    
    elif report_type == "Average Resolution Time":
        avg_time = st.session_state.db.get_average_resolution_time()
        st.metric("Average Resolution Time (hours)", f"{avg_time:.2f}")
    
    elif report_type == "Overdue Tickets":
        overdue = st.session_state.db.get_overdue_tickets()
        if overdue:
            df = pd.DataFrame(overdue, columns=[
                'ID', 'Title', 'Priority', 'Created', 'Status',
                'Time Limit (hrs)', 'Hours Elapsed'
            ])
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False)
            st.download_button("Download CSV", csv, "overdue_report.csv", "text/csv")
        else:
            st.success("No overdue tickets")
    
    elif report_type == "Status Distribution":
        stats = st.session_state.db.get_ticket_stats()
        df = pd.DataFrame(list(stats.items()), columns=['Status', 'Count'])
        
        st.dataframe(df, use_container_width=True)
        
        fig = px.pie(df, values='Count', names='Status', title='Ticket Status Distribution')
        st.plotly_chart(fig, use_container_width=True)

def system_settings():
    st.subheader("System Settings")
    
    tab1, tab2, tab3 = st.tabs(["Escalation Rules", "Technician Limits", "Archive"])
    
    with tab1:
        st.write("**Escalation Time Rules**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            high_hours = st.number_input("High Priority (hours)", min_value=1, value=4)
            if st.button("Update High"):
                st.session_state.db.update_escalation_rule('High', high_hours)
                st.success("Updated")
        
        with col2:
            medium_hours = st.number_input("Medium Priority (hours)", min_value=1, value=24)
            if st.button("Update Medium"):
                st.session_state.db.update_escalation_rule('Medium', medium_hours)
                st.success("Updated")
        
        low_hours = st.number_input("Low Priority (hours)", min_value=1, value=72)
        if st.button("Update Low"):
            st.session_state.db.update_escalation_rule('Low', low_hours)
            st.success("Updated")
    
    with tab2:
        st.write("**Set Maximum Open Tickets per Technician**")
        
        technicians = st.session_state.db.get_all_technicians()
        
        for tech in technicians:
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.write(tech[1])
            with col2:
                max_tickets = st.number_input(
                    f"Max tickets", 
                    min_value=1, 
                    value=20, 
                    key=f"max_{tech[0]}"
                )
            with col3:
                st.write("")
                if st.button("Set", key=f"set_{tech[0]}"):
                    st.session_state.db.set_technician_limit(tech[0], max_tickets)
                    st.success("Set")
    
    with tab3:
        st.write("**Archive Old Closed Tickets**")
        
        days = st.number_input("Archive tickets closed more than (days)", min_value=1, value=90)
        
        if st.button("Archive Old Tickets"):
            count = st.session_state.db.archive_old_tickets(days)
            st.success(f"Archived {count} tickets")

def main():
    st.set_page_config(
        page_title="IT Helpdesk System",
        page_icon="🎫",
        layout="wide"
    )
    
    init_session_state()
    
    if not st.session_state.logged_in:
        login_page()
    else:
        st.sidebar.title(f"Welcome {st.session_state.user['name']}")
        st.sidebar.write(f"Role: {st.session_state.user['role']}")
        
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()
        
        role = st.session_state.user['role']
        
        if role in ['Student', 'Faculty', 'Staff']:
            student_dashboard()
        elif role == 'Technician':
            technician_dashboard()
        elif role == 'Administrator':
            admin_dashboard()

if __name__ == "__main__":
    main()
