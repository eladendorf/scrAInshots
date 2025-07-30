#!/usr/bin/env python3
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import json
from api_server import APIServer
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Create a single instance of APIServer
api_server = APIServer()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

@app.route('/api/screenshots', methods=['GET'])
def get_screenshots():
    """Get screenshots with optional filtering"""
    query = request.args.get('q')
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    
    try:
        if query:
            results = api_server.db.search(query)
        elif start_date and end_date:
            results = api_server.db.get_by_date_range(start_date, end_date)
        else:
            results = api_server.db.get_all()
            
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error fetching screenshots: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/screenshots', methods=['POST'])
def process_screenshots():
    """Handle various screenshot operations"""
    data = request.get_json()
    action = data.get('action')
    
    try:
        if action == 'refine':
            # Refine a specific screenshot
            doc_id = data.get('id')
            prompt = data.get('prompt')
            
            # Get existing content
            doc = api_server.db.get_by_id(doc_id)
            if not doc:
                return jsonify({"error": "Document not found"}), 404
                
            # Use the refine_content method
            # This is a simplified version - you may want to make this async
            api_server.refine_content(doc_id, prompt)
            
            return jsonify({"success": True})
            
        else:
            return jsonify({"error": "Invalid action"}), 400
            
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/processing/start', methods=['POST'])
def start_processing():
    """Start batch processing"""
    try:
        result = api_server.start_batch_processing()
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error starting processing: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/processing/stop', methods=['POST'])
def stop_processing():
    """Stop batch processing"""
    try:
        result = api_server.stop_batch_processing()
        if "error" in result:
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error stopping processing: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/processing/status', methods=['GET'])
def get_processing_status():
    """Get processing status"""
    try:
        status = api_server.get_processing_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get overall statistics"""
    try:
        stats = api_server.batch_processor.get_statistics()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Flask API server on http://localhost:8000")
    app.run(host='0.0.0.0', port=8000, debug=False)