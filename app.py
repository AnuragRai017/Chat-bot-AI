from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from google.api_core import exceptions
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

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
model = genai.GenerativeModel('gemini-pro')

def create_prompt_context(employee_info, query):
    return f"""
    Based on the following employee information:
    {json.dumps(employee_info, indent=2)}
    
    Please answer the following query about salary deductions:
    {query}
    
    Provide a clear and detailed response focusing on the salary-related information requested.
    """

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

        # Verify API key is configured
        if not GOOGLE_API_KEY:
            return jsonify({'error': 'API key not configured'}), 500

        try:
            # Test API connection
            model = genai.GenerativeModel('gemini-pro')
            employee_info = employee_data[employee_id]
            prompt = create_prompt_context(employee_info, query)
            
            response = model.generate_content(prompt)
            
            if not response or not response.text:
                return jsonify({'error': 'No response from AI model'}), 500

            return jsonify({
                'employee_id': employee_id,
                'query': query,
                'response': response.text,
                'status': 'success'
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
                'status': 'api_error'
            }), 500

    except Exception as e:
        return jsonify({
            'error': f'Server Error: {str(e)}',
            'status': 'server_error'
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
