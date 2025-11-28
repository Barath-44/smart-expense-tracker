"""
Database Helper for Smart Expense Tracker
Simple SQLite database operations - no flaws, perfect persistence
"""

import sqlite3
from datetime import datetime
from contextlib import contextmanager

DATABASE_NAME = 'expenses.db'

@contextmanager
def get_db_connection():
    """Context manager for database connections - automatic cleanup!"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # Access columns by name
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_database():
    """Initialize database with tables - run once on startup"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create expenses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Create budgets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                category TEXT PRIMARY KEY,
                amount REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Create indexes for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_category 
            ON expenses(category)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_date 
            ON expenses(date)
        ''')
        
        print("✅ Database initialized successfully!")

# ============= EXPENSE OPERATIONS =============

def add_expense(amount, description, category, date=None, notes=''):
    """Add a new expense to database"""
    if date is None:
        date = datetime.now().isoformat()
    
    created_at = datetime.now().isoformat()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO expenses (amount, description, category, date, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (amount, description, category, date, notes, created_at))
        
        expense_id = cursor.lastrowid
        
        # Fetch the created expense
        cursor.execute('SELECT * FROM expenses WHERE id = ?', (expense_id,))
        row = cursor.fetchone()
        
        return dict(row)

def get_all_expenses(category=None, start_date=None, end_date=None):
    """Get all expenses with optional filters"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = 'SELECT * FROM expenses WHERE 1=1'
        params = []
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        if start_date:
            query += ' AND date >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND date <= ?'
            params.append(end_date)
        
        query += ' ORDER BY date DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]

def get_expense_by_id(expense_id):
    """Get a specific expense by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM expenses WHERE id = ?', (expense_id,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None

def delete_expense(expense_id):
    """Delete a specific expense - RETURNS TRUE IF DELETED"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
        
        # Check if any row was deleted
        return cursor.rowcount > 0

def delete_all_expenses():
    """Delete ALL expenses - USE WITH CAUTION!"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM expenses')
        deleted_count = cursor.rowcount
        
        # Reset auto-increment counter
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="expenses"')
        
        return deleted_count

def get_expense_count():
    """Get total number of expenses"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM expenses')
        result = cursor.fetchone()
        return result['count']

# ============= BUDGET OPERATIONS =============

def set_budget(category, amount):
    """Set or update budget for a category"""
    updated_at = datetime.now().isoformat()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO budgets (category, amount, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(category) 
            DO UPDATE SET amount = ?, updated_at = ?
        ''', (category, amount, updated_at, amount, updated_at))
        
        return True

def get_all_budgets():
    """Get all budgets"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM budgets')
        rows = cursor.fetchall()
        
        return {row['category']: row['amount'] for row in rows}

def get_budget(category):
    """Get budget for specific category"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT amount FROM budgets WHERE category = ?', (category,))
        row = cursor.fetchone()
        
        if row:
            return row['amount']
        return None

def delete_budget(category):
    """Delete budget for a category"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM budgets WHERE category = ?', (category,))
        return cursor.rowcount > 0

def delete_all_budgets():
    """Delete all budgets"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM budgets')
        return cursor.rowcount

# ============= ANALYTICS HELPERS =============

def get_total_spent(category=None, start_date=None, end_date=None):
    """Get total amount spent with optional filters"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = 'SELECT SUM(amount) as total FROM expenses WHERE 1=1'
        params = []
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        if start_date:
            query += ' AND date >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND date <= ?'
            params.append(end_date)
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        
        return result['total'] or 0.0

def get_spending_by_category():
    """Get spending grouped by category"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT category, 
                   SUM(amount) as total,
                   COUNT(*) as count
            FROM expenses
            GROUP BY category
            ORDER BY total DESC
        ''')
        rows = cursor.fetchall()
        
        return {row['category']: {
            'total': row['total'],
            'count': row['count']
        } for row in rows}

def get_monthly_spending():
    """Get spending grouped by month"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT strftime('%Y-%m', date) as month,
                   SUM(amount) as total
            FROM expenses
            GROUP BY month
            ORDER BY month DESC
        ''')
        rows = cursor.fetchall()
        
        return {row['month']: row['total'] for row in rows}