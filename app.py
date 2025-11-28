"""
Smart Expense Tracker with AI-Powered Insights
NOW WITH: SQLite Database + Delete Functionality
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

# Import database functions
from database import (
    init_database,
    add_expense as db_add_expense,
    get_all_expenses,
    get_expense_by_id,
    delete_expense as db_delete_expense,
    delete_all_expenses,
    get_expense_count,
    set_budget as db_set_budget,
    get_all_budgets,
    get_budget,
    get_total_spent,
    get_spending_by_category,
    get_monthly_spending
)

app = Flask(__name__)
CORS(app)

# Initialize database on startup
init_database()

# AI-like category keywords (simple but effective!)
CATEGORY_KEYWORDS = {
    'food': ['restaurant', 'cafe', 'food', 'pizza', 'burger', 'lunch', 'dinner', 'breakfast', 'starbucks', 'mcdonalds', 'subway', 'kfc'],
    'transport': ['uber', 'lyft', 'gas', 'fuel', 'parking', 'taxi', 'metro', 'bus', 'train', 'ola'],
    'shopping': ['amazon', 'walmart', 'target', 'mall', 'store', 'shop', 'clothing', 'shoes', 'flipkart'],
    'entertainment': ['netflix', 'spotify', 'movie', 'cinema', 'game', 'concert', 'theater', 'prime'],
    'utilities': ['electricity', 'water', 'internet', 'phone', 'wifi', 'bill'],
    'health': ['pharmacy', 'hospital', 'doctor', 'medical', 'gym', 'fitness', 'medicine'],
    'education': ['book', 'course', 'tuition', 'school', 'university', 'training', 'udemy']
}

# Helper Functions

def smart_categorize(description):
    """AI-like categorization based on keywords"""
    description_lower = description.lower()
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in description_lower:
                return category
    
    return 'other'

def predict_next_month_spending():
    """Simple ML-like prediction using historical average"""
    monthly_spending = get_monthly_spending()
    
    if not monthly_spending:
        return 0
    
    if len(monthly_spending) < 2:
        return list(monthly_spending.values())[0] if monthly_spending else 0
    
    # Calculate average with trend
    totals = list(monthly_spending.values())
    avg = statistics.mean(totals)
    
    # Simple trend analysis
    if len(totals) >= 3:
        recent_avg = statistics.mean(totals[:3])  # Last 3 months
        trend = (recent_avg - avg) * 0.3
        return round(avg + trend, 2)
    
    return round(avg, 2)

def detect_anomalies():
    """Detect unusual spending patterns"""
    expenses = get_all_expenses()
    
    if len(expenses) < 10:
        return []
    
    amounts = [exp['amount'] for exp in expenses]
    mean = statistics.mean(amounts)
    stdev = statistics.stdev(amounts) if len(amounts) > 1 else 0
    
    anomalies = []
    for exp in expenses[:20]:  # Check last 20 transactions
        if stdev > 0 and exp['amount'] > mean + (2 * stdev):
            anomalies.append({
                'expense': exp,
                'reason': f"Unusually high amount (${exp['amount']:.2f} vs average ${mean:.2f})"
            })
    
    return anomalies

def generate_insights():
    """Generate smart insights from spending data"""
    expenses = get_all_expenses()
    
    if not expenses:
        return []
    
    insights = []
    
    # Category analysis
    category_totals = get_spending_by_category()
    total_spent = sum(cat['total'] for cat in category_totals.values())
    
    # Find top spending category
    if category_totals:
        top_category = max(category_totals.items(), key=lambda x: x[1]['total'])
        top_name = top_category[0]
        top_amount = top_category[1]['total']
        top_percentage = (top_amount / total_spent) * 100
        
        insights.append({
            'type': 'category_insight',
            'message': f"Your highest spending is on {top_name} (${top_amount:.2f}, {top_percentage:.1f}% of total)",
            'icon': '📊'
        })
    
    # Recent spending trend
    recent_expenses = [exp for exp in expenses if 
                      datetime.fromisoformat(exp['date']) > datetime.now() - timedelta(days=7)]
    if recent_expenses:
        recent_total = sum(exp['amount'] for exp in recent_expenses)
        daily_avg = recent_total / 7
        
        insights.append({
            'type': 'trend',
            'message': f"You've spent ${recent_total:.2f} this week (${daily_avg:.2f}/day average)",
            'icon': '📈'
        })
    
    # Savings suggestion
    if len(expenses) > 5:
        avg_expense = statistics.mean([exp['amount'] for exp in expenses])
        savings_potential = avg_expense * 0.1 * 30
        
        insights.append({
            'type': 'savings',
            'message': f"By reducing spending by 10%, you could save ${savings_potential:.2f} per month",
            'icon': '💰'
        })
    
    return insights

# API Routes

@app.route('/')
def home():
    """API Documentation"""
    expense_count = get_expense_count()
    
    return jsonify({
        'name': 'Smart Expense Tracker API',
        'version': '2.0',
        'database': 'SQLite',
        'total_expenses': expense_count,
        'features': [
            'AI-powered auto-categorization',
            'Smart spending predictions',
            'Anomaly detection',
            'Budget tracking with alerts',
            'Intelligent insights',
            'Delete individual expenses',
            'Delete all expenses',
            'SQLite database storage'
        ],
        'endpoints': {
            'POST /expense': 'Add new expense',
            'GET /expenses': 'Get all expenses',
            'GET /expense/<id>': 'Get specific expense',
            'DELETE /expense/<id>': 'Delete specific expense',
            'DELETE /expenses/all': 'Delete ALL expenses',
            'GET /analytics': 'Get spending analytics',
            'GET /insights': 'Get AI-powered insights',
            'GET /predict': 'Predict next month spending',
            'POST /budget': 'Set category budget',
            'GET /budget-status': 'Check budget status'
        }
    })

@app.route('/expense', methods=['POST'])
def add_expense():
    """Add a new expense with auto-categorization"""
    data = request.get_json()
    
    # Validation
    if not data or 'amount' not in data or 'description' not in data:
        return jsonify({'error': 'Amount and description are required'}), 400
    
    try:
        amount = float(data['amount'])
        if amount <= 0:
            return jsonify({'error': 'Amount must be positive'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid amount format'}), 400
    
    description = data['description']
    category = data.get('category') or smart_categorize(description)
    notes = data.get('notes', '')
    date = data.get('date')
    
    # Add to database
    expense = db_add_expense(amount, description, category, date, notes)
    
    # Check budget
    budget = get_budget(category)
    budget_alert = None
    
    if budget:
        category_total = get_total_spent(category=category)
        percentage = (category_total / budget) * 100
        
        if percentage >= 90:
            budget_alert = {
                'level': 'critical' if percentage >= 100 else 'warning',
                'message': f"Budget alert: {percentage:.1f}% of {category} budget used (${category_total:.2f}/${budget})"
            }
    
    return jsonify({
        'success': True,
        'expense': expense,
        'auto_categorized': 'category' not in data or not data['category'],
        'budget_alert': budget_alert
    }), 201

@app.route('/expenses', methods=['GET'])
def get_expenses():
    """Get all expenses with optional filters"""
    category = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    expenses = get_all_expenses(category, start_date, end_date)
    
    # Calculate summary
    total = sum(exp['amount'] for exp in expenses)
    by_category = get_spending_by_category()
    
    return jsonify({
        'expenses': expenses,
        'summary': {
            'total': round(total, 2),
            'count': len(expenses),
            'by_category': by_category
        }
    })

@app.route('/expense/<int:expense_id>', methods=['GET'])
def get_expense(expense_id):
    """Get a specific expense"""
    expense = get_expense_by_id(expense_id)
    
    if not expense:
        return jsonify({'error': 'Expense not found'}), 404
    
    return jsonify(expense)

@app.route('/expense/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    """Delete a specific expense"""
    deleted = db_delete_expense(expense_id)
    
    if not deleted:
        return jsonify({'error': 'Expense not found'}), 404
    
    return jsonify({
        'success': True,
        'message': f'Expense {expense_id} deleted successfully',
        'deleted_id': expense_id
    })

@app.route('/expenses/all', methods=['DELETE'])
def delete_all():
    """Delete ALL expenses - USE WITH CAUTION!"""
    count = delete_all_expenses()
    
    return jsonify({
        'success': True,
        'message': f'All expenses deleted successfully',
        'deleted_count': count
    })

@app.route('/analytics', methods=['GET'])
def get_analytics():
    """Get comprehensive spending analytics"""
    expenses = get_all_expenses()
    
    if not expenses:
        return jsonify({'message': 'No expenses yet'})
    
    total_spent = sum(exp['amount'] for exp in expenses)
    avg_expense = total_spent / len(expenses)
    
    # Category breakdown
    by_category_raw = get_spending_by_category()
    by_category = {}
    for cat, data in by_category_raw.items():
        by_category[cat] = {
            'total': round(data['total'], 2),
            'count': data['count'],
            'percentage': round((data['total'] / total_spent) * 100, 1)
        }
    
    # Monthly trend
    by_month = get_monthly_spending()
    monthly_trend = {month: round(total, 2) for month, total in by_month.items()}
    
    # Recent activity (last 30 days)
    thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
    recent_total = get_total_spent(start_date=thirty_days_ago)
    
    return jsonify({
        'overall': {
            'total_spent': round(total_spent, 2),
            'total_transactions': len(expenses),
            'average_expense': round(avg_expense, 2),
            'last_30_days': round(recent_total, 2)
        },
        'by_category': by_category,
        'monthly_trend': monthly_trend
    })

@app.route('/insights', methods=['GET'])
def get_insights():
    """Get AI-powered spending insights"""
    insights = generate_insights()
    anomalies = detect_anomalies()
    
    return jsonify({
        'insights': insights,
        'anomalies': anomalies,
        'generated_at': datetime.now().isoformat()
    })

@app.route('/predict', methods=['GET'])
def predict_spending():
    """Predict next month's spending using ML-like algorithm"""
    prediction = predict_next_month_spending()
    expense_count = get_expense_count()
    
    # Per category predictions
    category_spending = get_spending_by_category()
    category_predictions = {}
    for category, data in category_spending.items():
        category_predictions[category] = round(data['total'] / max(len(get_monthly_spending()), 1), 2)
    
    confidence = 'high' if expense_count > 30 else 'medium' if expense_count > 10 else 'low'
    
    return jsonify({
        'prediction': {
            'total': prediction,
            'by_category': category_predictions,
            'confidence': confidence,
            'based_on_transactions': expense_count
        },
        'recommendation': f"Based on your spending patterns, budget ${prediction * 1.1:.2f} to be safe"
    })

@app.route('/budget', methods=['POST'])
def set_budget():
    """Set budget for a category"""
    data = request.get_json()
    
    if not data or 'category' not in data or 'amount' not in data:
        return jsonify({'error': 'Category and amount are required'}), 400
    
    category = data['category']
    amount = float(data['amount'])
    
    db_set_budget(category, amount)
    
    return jsonify({
        'success': True,
        'message': f"Budget set for {category}: ${amount}"
    })

@app.route('/budget-status', methods=['GET'])
def get_budget_status():
    """Check budget status for all categories"""
    budgets = get_all_budgets()
    
    if not budgets:
        return jsonify({'message': 'No budgets set yet'})
    
    # Get current month spending
    current_month = datetime.now().strftime('%Y-%m')
    current_month_start = current_month + '-01'
    
    status = {}
    for category, budget in budgets.items():
        spent = get_total_spent(category=category, start_date=current_month_start)
        percentage = (spent / budget) * 100 if budget > 0 else 0
        remaining = budget - spent
        
        status[category] = {
            'budget': budget,
            'spent': round(spent, 2),
            'remaining': round(remaining, 2),
            'percentage': round(percentage, 1),
            'status': 'exceeded' if percentage > 100 else 'warning' if percentage > 80 else 'good'
        }
    
    return jsonify({
        'month': current_month,
        'budgets': status
    })

@app.route('/export', methods=['GET'])
def export_data():
    """Export all data"""
    expenses = get_all_expenses()
    budgets = get_all_budgets()
    
    return jsonify({
        'expenses': expenses,
        'budgets': budgets,
        'total_expenses': len(expenses),
        'exported_at': datetime.now().isoformat()
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    """Quick stats for dashboard"""
    expense_count = get_expense_count()
    total_spent = get_total_spent()
    
    return jsonify({
        'total_expenses': expense_count,
        'total_spent': round(total_spent, 2),
        'database_size': f"{expense_count} records"
    })

if __name__ == '__main__':
    print("💰 Smart Expense Tracker API Starting...")
    print("🗄️  SQLite Database Active")
    print("📊 AI-Powered Analytics & Predictions Active")
    print("🗑️  Delete Functions Enabled")
    print("🚀 Server running on http://localhost:5000")
    app.run(debug=True, port=5000)