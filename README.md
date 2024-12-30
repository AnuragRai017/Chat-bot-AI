# Salary ChatBot

A Flask-based application that processes Excel files containing employee salary data and converts them into a structured JSON database.

## Features

- Convert Excel files to JSON format
- Combine multiple Excel sheets into a single database
- Process employee salary, attendance, and leave data
- RESTful API endpoints for data processing

## Installation

```bash
# Clone the repository
git clone https://github.com/AnuragRai017/Chat-bot-AI.git
cd Chat-bot-AI

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
copy .env.example .env
# Update .env with your configurations
```

## Usage

```bash
# Run the Flask application
python app.py
```

## API Endpoints

- `GET /`: Health check endpoint
- `POST /process`: Process Excel files and generate JSON database

## Project Structure

```
Salary_chat_bot/
├── app.py              # Flask application
├── excel_to_json.py    # Excel processing logic
├── requirements.txt    # Project dependencies
└── wsgi.py            # WSGI entry point
```

## Dependencies

- Flask
- Pandas
- Python-dotenv
- Openpyxl

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.