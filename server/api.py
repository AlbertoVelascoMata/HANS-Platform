import json
from threading import Thread
from pathlib import Path

from flask import Flask, request, send_file, jsonify, send_from_directory
from werkzeug.serving import make_server

QUESTIONS_FOLDER = Path('questions')
SESSION_DETAILS = {
    '1': {
        'question': '1',
        'duration': 30,
        'status': 'inactive'
    },
    '2': {
        'question': '2',
        'duration': 30,
        'status': 'inactive'
    }
}

class ServerAPI(Thread):
    def __init__(self, host='0.0.0.0', port=5000):
        Thread.__init__(self)
        self.app = Flask(__name__)

        @self.app.route('/')
        def index_handle():
            return send_from_directory('../client', 'index.html')

        @self.app.route('/api/session/<int:session_id>')
        def session_handle(session_id: int):
            if str(session_id) not in SESSION_DETAILS:
                return "Session not found", 404
            
            return jsonify(SESSION_DETAILS[str(session_id)])

        @self.app.route('/api/question/<int:question_id>/image')
        def question_image_handle(question_id: int):
            question_folder = QUESTIONS_FOLDER / str(question_id)
            if not question_folder.is_dir():
                return "Question not found", 404

            img_path = next(question_folder.glob('img.*'))
            if not img_path.is_file():
                return "Image not found for this question", 500
            
            return send_file(img_path)
        
        @self.app.route('/api/question/<int:question_id>')
        def question_handle(question_id: int):
            question_folder = QUESTIONS_FOLDER / str(question_id)
            if not question_folder.is_dir():
                return "Question not found", 404

            info_path = question_folder / 'info.json'
            if not info_path.is_file():
                return "Question info not found", 500
            
            with open(info_path, 'r') as f:
                data = json.load(f)
            return jsonify(data)

        self.server = make_server(host, port, self.app)
        self.ctx = self.app.app_context()
        self.ctx.push()

        self.on_start = None
    
    def run(self):
        if callable(self.on_start): self.on_start(self)
        self.server.serve_forever()
    
    def shutdown(self):
        self.server.shutdown()
