#!/usr/bin/env python3
"""
Gate Control System - Webhook Server with Web Frontend
Receives incoming call notifications from 46elks and triggers Home Assistant webhook
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/gate_control.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
HOME_ASSISTANT_URL = os.getenv('HOME_ASSISTANT_URL')
HOME_ASSISTANT_WEBHOOK_ID = os.getenv('HOME_ASSISTANT_WEBHOOK_ID')
TRUSTED_NUMBERS_FILE = 'config/trusted_numbers.json'
CALL_LOG_FILE = 'logs/call_attempts.log'


def load_trusted_numbers():
    """Load trusted phone numbers from JSON file"""
    try:
        with open(TRUSTED_NUMBERS_FILE, 'r') as f:
            data = json.load(f)
            return set(data.get('numbers', []))
    except FileNotFoundError:
        logger.error(f"Trusted numbers file not found: {TRUSTED_NUMBERS_FILE}")
        return set()
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in trusted numbers file: {TRUSTED_NUMBERS_FILE}")
        return set()


def is_number_trusted(phone_number):
    """Check if a phone number is in the trusted list"""
    trusted_numbers = load_trusted_numbers()
    return phone_number in trusted_numbers


def trigger_home_assistant_gate():
    """Send webhook request to Home Assistant to open the gate"""
    if not HOME_ASSISTANT_URL or not HOME_ASSISTANT_WEBHOOK_ID:
        logger.error("Home Assistant configuration missing")
        return False
    
    webhook_url = f"{HOME_ASSISTANT_URL}/api/webhook/{HOME_ASSISTANT_WEBHOOK_ID}"
    
    try:
        payload = {
            "action": "open_gate",
            "timestamp": datetime.now().isoformat(),
            "source": "phone_call"
        }
        
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("Successfully triggered Home Assistant gate webhook")
            return True
        else:
            logger.error(f"Home Assistant webhook failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to call Home Assistant webhook: {e}")
        return False


def log_call_attempt(caller_number, trusted, gate_opened):
    """Log call attempt to file for security monitoring"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "caller": caller_number,
        "trusted": trusted,
        "gate_opened": gate_opened
    }
    
    try:
        with open(CALL_LOG_FILE, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        logger.error(f"Failed to write call attempt log: {e}")


def read_call_logs(limit=50):
    """Read recent call attempts from log file"""
    try:
        if not os.path.exists(CALL_LOG_FILE):
            return []
        
        with open(CALL_LOG_FILE, 'r') as f:
            lines = f.readlines()
        
        # Get last N lines and parse JSON
        logs = []
        for line in reversed(lines[-limit:]):
            try:
                log_entry = json.loads(line.strip())
                logs.append(log_entry)
            except json.JSONDecodeError:
                continue
        
        return logs
    except Exception as e:
        logger.error(f"Failed to read call logs: {e}")
        return []


# ============================================================================
# WEB FRONTEND ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main admin dashboard"""
    return render_template('index.html')


@app.route('/admin/stats')
def get_stats():
    """Get statistics for dashboard"""
    logs = read_call_logs(limit=1000)
    
    total_calls = len(logs)
    successful_calls = sum(1 for log in logs if log.get('gate_opened', False))
    
    return jsonify({
        "total_calls": total_calls,
        "successful_calls": successful_calls,
        "denied_calls": total_calls - successful_calls
    })


@app.route('/admin/logs')
def get_logs():
    """Get recent call logs"""
    logs = read_call_logs(limit=100)
    return jsonify({
        "logs": logs,
        "count": len(logs)
    })


@app.route('/admin/trusted-numbers', methods=['GET'])
def get_trusted_numbers():
    """Get list of trusted numbers"""
    trusted_numbers = list(load_trusted_numbers())
    trusted_numbers.sort()  # Sort alphabetically
    return jsonify({
        "numbers": trusted_numbers,
        "count": len(trusted_numbers)
    })


@app.route('/admin/add-number', methods=['POST'])
def add_trusted_number():
    """Add a number to the trusted list"""
    data = request.get_json()
    new_number = data.get('number', '').strip()
    
    if not new_number:
        return jsonify({"error": "Inget nummer angivet"}), 400
    
    if not new_number.startswith('+'):
        return jsonify({"error": "Nummer måste vara i E.164 format (börja med +)"}), 400
    
    # Basic validation
    if len(new_number) < 10 or len(new_number) > 16:
        return jsonify({"error": "Ogiltigt telefonnummer"}), 400
    
    try:
        with open(TRUSTED_NUMBERS_FILE, 'r') as f:
            config = json.load(f)
        
        if new_number in config['numbers']:
            return jsonify({"message": "Numret finns redan"}), 200
        
        config['numbers'].append(new_number)
        
        with open(TRUSTED_NUMBERS_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Added trusted number: {new_number}")
        return jsonify({"message": "Nummer tillagt"}), 200
        
    except Exception as e:
        logger.error(f"Failed to add number: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/remove-number', methods=['POST'])
def remove_trusted_number():
    """Remove a number from the trusted list"""
    data = request.get_json()
    number_to_remove = data.get('number', '').strip()
    
    if not number_to_remove:
        return jsonify({"error": "Inget nummer angivet"}), 400
    
    try:
        with open(TRUSTED_NUMBERS_FILE, 'r') as f:
            config = json.load(f)
        
        if number_to_remove not in config['numbers']:
            return jsonify({"error": "Numret finns inte"}), 404
        
        config['numbers'].remove(number_to_remove)
        
        with open(TRUSTED_NUMBERS_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Removed trusted number: {number_to_remove}")
        return jsonify({"message": "Nummer borttaget"}), 200
        
    except Exception as e:
        logger.error(f"Failed to remove number: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# 46ELKS WEBHOOK ROUTES
# ============================================================================

@app.route('/elks/incoming-call', methods=['POST'])
def handle_incoming_call():
    """
    Handle incoming call webhook from 46elks
    
    Expected parameters from 46elks:
    - callid: Unique call ID
    - from: Caller's phone number (E.164 format)
    - to: Your 46elks number
    - direction: "incoming"
    - created: Timestamp
    """
    
    # Get call data from 46elks
    call_data = request.form.to_dict()
    
    caller_number = call_data.get('from', '')
    callid = call_data.get('callid', '')
    
    logger.info(f"Incoming call from {caller_number} (Call ID: {callid})")
    
    # Check if number is trusted
    is_trusted = is_number_trusted(caller_number)
    gate_opened = False
    
    if is_trusted:
        logger.info(f"Trusted number detected: {caller_number}")
        
        # Trigger Home Assistant to open gate
        gate_opened = trigger_home_assistant_gate()
        
        if gate_opened:
            logger.info(f"Gate opened for {caller_number}")
        else:
            logger.error(f"Failed to open gate for {caller_number}")
    else:
        logger.warning(f"Untrusted number attempted access: {caller_number}")
    
    # Log the attempt
    log_call_attempt(caller_number, is_trusted, gate_opened)
    
    # Respond to 46elks with call action
    # Just hangup immediately - the gate is already opening
    response = {
        "hangup": "true"
    }
    
    return jsonify(response), 200


@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        "status": "healthy",
        "service": "Gate Control System",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })


if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('config', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # Get port from environment or use default
    port = int(os.getenv('SERVER_PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Gate Control System on port {port}")
    logger.info(f"Home Assistant URL: {HOME_ASSISTANT_URL}")
    
    # Load and display trusted numbers count
    trusted_count = len(load_trusted_numbers())
    logger.info(f"Loaded {trusted_count} trusted phone numbers")
    
    logger.info(f"Web interface available at: http://localhost:{port}/")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
