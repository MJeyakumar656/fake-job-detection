from flask import Flask, render_template, request, jsonify, session, redirect
from flask_cors import CORS
import os
from dotenv import load_dotenv
from routes import api_bp

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Configure session
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Register blueprints
app.register_blueprint(api_bp)

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/result')
def result():
    """Result page"""
    # Get last analysis from session
    analysis = session.get('last_analysis', {})
    
    if not analysis:
        return redirect('/')
    
    return render_template('result.html', result=analysis)

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/how-it-works')
def how_it_works():
    """How it works page"""
    return render_template('how_it_works.html')

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Page not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('models', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)