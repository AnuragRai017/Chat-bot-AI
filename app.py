from flask import Flask, request, jsonify, render_template, session
import google.generativeai as genai
from google.api_core import exceptions
import json
import os
from dotenv import load_dotenv
from flask_session import Session
from collections import defaultdict
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure server-side session
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Initialize chat history cache
chat_history_cache = defaultdict(list)
CACHE_DURATION_DAYS = 7

# Load employee data from JSON file
EMPLOYEE_DATA_FILE = 'employee_database.json'
if not os.path.exists(EMPLOYEE_DATA_FILE):
    raise FileNotFoundError(f"Employee database file {EMPLOYEE_DATA_FILE} not found")

with open(EMPLOYEE_DATA_FILE, 'r') as f:
    employee_data = json.load(f)

# Configure Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

# Initialize the API client with correct configuration
genai.configure(api_key=GOOGLE_API_KEY)

# Use the latest stable model version
model = genai.GenerativeModel('gemini-2.0-flash-exp')

def calculate_monthly_deductions(yearly_deductions):
    """Convert yearly deductions to monthly values."""
    monthly_deductions = {}
    for key, value in yearly_deductions.items():
        if isinstance(value, (int, float)):
            monthly_deductions[key] = round(value / 12, 2)
        else:
            monthly_deductions[key] = value
    return monthly_deductions

def create_prompt_context(employee_info, query):
    # Add monthly calculations to employee info
    employee_info_with_monthly = employee_info.copy()
    
    # Calculate monthly values for all salary components
    monthly_components = {}
    yearly_components = ['Basic Salary', 'HRA', 'Special Allowance', 'LTA', 'Uniform Allowance']
    for comp in yearly_components:
        if comp in employee_info:
            monthly_components[comp] = round(employee_info[comp] / 12, 2)
    
    employee_info_with_monthly['monthly_components'] = monthly_components

    # Add tax slab information
    tax_slabs = {
        "0-2.5L": "No tax",
        "2.5L-5L": "5%",
        "5L-7.5L": "10%",
        "7.5L-10L": "15%",
        "10L-12.5L": "20%",
        "12.5L-15L": "25%",
        "Above 15L": "30%"
    }
    
    # Add deduction explanations
    deduction_explanations = {
        "PF": {
            "rate": "12% of Basic Salary",
            "purpose": "Long-term retirement savings with tax benefits",
            "employer_contribution": "Equal contribution from employer",
            "withdrawal": "Withdrawable after retirement or specific conditions"
        },
        "Income Tax": {
            "calculation": "Based on tax slabs after standard deduction",
            "slabs": tax_slabs,
            "deductions": "Section 80C, HRA, LTA can reduce taxable income"
        },
        "Professional Tax": {
            "type": "State-specific tax",
            "frequency": "Monthly deduction",
            "purpose": "Contribution to state revenue"
        }
    }
    
    # Add allowance explanations
    allowance_explanations = {
        "HRA": {
            "purpose": "For rental accommodation expenses",
            "tax_benefit": "Tax exemption available with rent receipts",
            "calculation": "40% of Basic Salary for non-metro cities, 50% for metros"
        },
        "LTA": {
            "purpose": "For travel expenses within India",
            "frequency": "Can be claimed twice in a block of 4 years",
            "tax_benefit": "Tax-free if proper bills are submitted"
        },
        "Special Allowance": {
            "purpose": "Additional monetary benefit",
            "taxability": "Fully taxable",
            "flexibility": "Can be used for any purpose"
        }
    }

    employee_info_with_monthly['deduction_explanations'] = deduction_explanations
    employee_info_with_monthly['allowance_explanations'] = allowance_explanations
    
    return f"""
    You are a helpful salary assistant. Based on the employee information and explanations provided below, answer the query in a conversational and informative way.
    
    Employee Information:
    {json.dumps(employee_info_with_monthly, indent=2)}

    When answering questions about:

    1. PF (Provident Fund):
    - Explain it's a retirement benefit
    - Show calculation: 12% of Basic Salary
    - Mention employer's equal contribution
    - Explain tax benefits
    
    2. Income Tax:
    - Explain which tax slab applies
    - Break down the calculation
    - Mention available deductions
    - Explain how to optimize tax
    
    3. Allowances (HRA, LTA, etc.):
    - Explain their purpose
    - Show how they're calculated
    - Mention tax implications
    - Provide usage guidelines
    
    4. Deductions:
    - Explain why each deduction is made
    - Show the calculation method
    - Compare with previous months if relevant
    - Suggest ways to optimize
    
    5. Leave and Attendance:
    - Explain leave balance and usage
    - Show impact on salary
    - Explain leave policies
    - Suggest leave planning

    Format your response with:
    - Use <salary>amount</salary> for salary components
    - Use <deduction>amount</deduction> for deductions
    - Use <bold>text</bold> for important information
    - Always show both yearly and monthly figures where applicable
    - Format all currency values with ₹ symbol
    - Use bullet points for better readability
    
    Current Query: {query}
    
    Respond in a friendly, helpful manner. If the query is about calculations, show the step-by-step process. If it's about policies, explain them clearly with examples.
    """

def is_deduction_query(query):
    """Check if the query is related to deductions or amounts"""
    deduction_keywords = ['deduction', 'amount', 'salary', 'pay', 'cut', 'tax', 'pf', 'professional tax']
    return any(keyword in query.lower() for keyword in deduction_keywords)

def format_deduction_table(employee_info, is_yearly=False):
    """Create an HTML table for deductions"""
    # Calculate monthly salary components first
    monthly_basic = employee_info.get('Basic Salary', 0) / 12
    
    # Calculate deductions
    monthly_deductions = {
        'PF (Provident Fund)': round(monthly_basic * 0.12, 2),
        'Income Tax': round(monthly_basic * 0.2, 2),  # Simplified calculation
        'Professional Tax': 200
    }
    
    # If yearly is requested, multiply monthly values by 12
    if is_yearly:
        deductions = {
            key: round(value * 12, 2) if key != 'Professional Tax' else value * 12
            for key, value in monthly_deductions.items()
        }
        period = "Yearly"
    else:
        deductions = monthly_deductions
        period = "Monthly"
    
    table_html = f"""
    <table class="deduction-table">
        <thead>
            <tr>
                <th>Type of Deduction ({period})</th>
                <th>Amount (₹)</th>
                <th>Calculation Basis</th>
                <th>Purpose</th>
            </tr>
        </thead>
        <tbody>
    """
    
    details = {
        'PF (Provident Fund)': {
            'calc': '12% of Basic Salary',
            'purpose': 'Retirement benefit and tax-free savings'
        },
        'Income Tax': {
            'calc': '20% of taxable income',
            'purpose': 'Government tax on income'
        },
        'Professional Tax': {
            'calc': f'Fixed amount ({period})',
            'purpose': 'State-specific professional levy'
        }
    }
    
    for deduction_type, amount in deductions.items():
        table_html += f"""
            <tr>
                <td><strong>{deduction_type}</strong></td>
                <td>₹{amount:,.2f}</td>
                <td>{details[deduction_type]['calc']}</td>
                <td>{details[deduction_type]['purpose']}</td>
            </tr>
        """
    
    table_html += """
        </tbody>
    </table>
    """
    return table_html

def format_response_with_html(text, query, employee_info):
    """Format the response with appropriate HTML styling"""
    if is_deduction_query(query):
        try:
            # Check if the query is about yearly deductions
            is_yearly = 'year' in query.lower()
            return format_deduction_table(employee_info, is_yearly)
        except Exception as e:
            # Fallback to regular text format if there's an error
            return f'<div class="response-text">{text}</div>'
    else:
        # Format regular responses with bold and highlighting
        formatted_text = text.replace('**', '<strong>').replace('**', '</strong>')
        return f'<div class="response-text">{formatted_text}</div>'

def update_chat_history(employee_id, query, response):
    """Update chat history with timestamp and maintain 7-day limit."""
    current_time = datetime.now()
    chat_history_cache[employee_id].append({
        'timestamp': current_time,
        'query': query,
        'response': response
    })
    
    # Remove entries older than 7 days
    cutoff_time = current_time - timedelta(days=CACHE_DURATION_DAYS)
    chat_history_cache[employee_id] = [
        entry for entry in chat_history_cache[employee_id]
        if entry['timestamp'] > cutoff_time
    ]

def get_recent_chat_history(employee_id):
    """Get chat history for the past 7 days."""
    return [
        {
            'query': entry['query'],
            'response': entry['response'],
            'timestamp': entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        }
        for entry in chat_history_cache[employee_id]
    ]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        query = data.get('query')

        if not employee_id or not query:
            return jsonify({'error': 'Missing employee_id or query'}), 400

        if employee_id not in employee_data:
            return jsonify({'error': 'Employee ID not found'}), 404

        employee_info = employee_data[employee_id]
        prompt = create_prompt_context(employee_info, query)

        try:
            response = model.generate_content(prompt)
            if not response or not response.text:
                return jsonify({'error': 'No response from AI model'}), 500

            # Format the response with HTML tags
            formatted_response = format_response_with_html(response.text, query, employee_info)
            
            # Update chat history cache
            update_chat_history(employee_id, query, formatted_response)
            
            # Get recent chat history
            history = get_recent_chat_history(employee_id)

            return jsonify({
                'employee_id': employee_id,
                'query': query,
                'response': formatted_response,
                'history': history
            })

        except exceptions.InvalidArgument:
            return jsonify({
                'error': 'Invalid API key or authentication failed. Please check your Google AI Studio API key.',
                'status': 'auth_error'
            }), 401
        except exceptions.PermissionDenied:
            return jsonify({
                'error': 'Permission denied. Please verify API key permissions.',
                'status': 'permission_error'
            }), 403
        except Exception as api_error:
            return jsonify({
                'error': f'API Error: {str(api_error)}',
                'status': 'error'
            }), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
