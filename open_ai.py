from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from google.api_core import exceptions
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import random
from openai import OpenAI
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Load employee data
EMPLOYEE_DATA_FILE = 'employee_database.json'
if not os.path.exists(EMPLOYEE_DATA_FILE):
    raise FileNotFoundError(f"Employee database file {EMPLOYEE_DATA_FILE} not found")

with open(EMPLOYEE_DATA_FILE, 'r') as f:
    employee_data = json.load(f)

# Configure OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in .env file")

client = OpenAI(api_key=OPENAI_API_KEY)

# Configure Gemini API for backup
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Predefined response templates with embeddings
RESPONSE_TEMPLATES = {
    'salary': [
        "Let me show you your salary breakdown 💰",
        "Here's a detailed view of your compensation 📊",
        "I'll break down your salary components 💳",
        "Here's how your salary package looks 📈"
    ],
    'deductions': [
        "Let me explain your deductions 📋",
        "Here's what's being deducted from your salary 💸",
        "Let's look at your salary deductions 🔍",
        "Here's a breakdown of your deductions 📊"
    ],
    'calculations': [
        "Let me explain how this is calculated 🧮",
        "Here's how we compute these numbers 📱",
        "The calculation works like this ✨",
        "Let me break down the calculation process 📝"
    ]
}

def get_embedding(text):
    """Get embedding for text using OpenAI's API"""
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return None

def find_best_response_category(query):
    """Find the most relevant response category using embeddings"""
    query_embedding = get_embedding(query)
    if not query_embedding:
        return None

    # Predefined category embeddings
    category_texts = {
        'salary': "salary compensation package pay earnings income",
        'deductions': "deductions tax PF professional tax take home net salary",
        'calculations': "calculate compute how determined formula method"
    }
    
    category_embeddings = {
        category: get_embedding(text)
        for category, text in category_texts.items()
    }
    
    # Calculate similarities
    similarities = {
        category: cosine_similarity(
            [query_embedding],
            [embedding]
        )[0][0]
        for category, embedding in category_embeddings.items()
        if embedding is not None
    }
    
    # Return category with highest similarity
    if similarities:
        return max(similarities.items(), key=lambda x: x[1])[0]
    return None

def create_dynamic_response(employee_info, query):
    """Create a dynamic response using embeddings for context understanding"""
    category = find_best_response_category(query)
    if not category:
        return create_fallback_response(employee_info, query)
    
    # Get random greeting from appropriate category
    greeting = random.choice(RESPONSE_TEMPLATES[category])
    
    if category == 'salary':
        return create_salary_response(employee_info, greeting)
    elif category == 'deductions':
        return create_deduction_response(employee_info, query, greeting)
    elif category == 'calculations':
        return create_calculation_response(employee_info, query)
    
    return create_fallback_response(employee_info, query)

def create_calculation_response(employee_info, query):
    """Create a response explaining calculations"""
    explanations = get_deduction_explanation()
    
    if 'pf' in query.lower():
        return f"""Let me explain how your PF is calculated 🧮

{explanations['pf']}

For your salary:
Basic Salary: {format_currency(employee_info['Basic Salary'] / 12)} per month
Monthly PF (12%): {format_currency(calculate_monthly_data(employee_info)['pf_deduction'])}

This contribution helps build your retirement savings! 💰
Would you like to know about other calculations? 🤔"""
    
    if 'tax' in query.lower():
        return f"""Here's how your income tax is calculated 📊

{explanations['tax']}

Your Annual Income: {format_currency(employee_info['CTC'])}
Monthly Tax Deduction: {format_currency(calculate_monthly_data(employee_info)['income_tax'])}

Want to learn about tax-saving investments? Just ask! 💡"""
    
    return f"""Let me explain how your deductions are calculated 🎯

1. PF Calculation:
{explanations['pf']}

2. Income Tax:
{explanations['tax']}

3. Professional Tax:
{explanations['professional']}

Which calculation would you like me to explain in detail? 🤔"""

def create_fallback_response(employee_info, query):
    """Create a fallback response using Gemini AI"""
    try:
        response = model.generate_content(
            f"You are a helpful salary assistant. The user asked: {query}. "
            "Respond in a friendly, concise way."
        )
        return response.text
    except:
        return """I'm here to help! 👋 You can ask me about:

1. Your salary details 💰
2. Deductions breakdown 📊
3. How calculations work 🧮

What would you like to know? 😊"""