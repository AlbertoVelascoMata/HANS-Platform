from pathlib import Path
from threading import Thread

from flask import (Flask, jsonify, redirect, request, send_file,
                   send_from_directory)
from PyQt5.QtCore import QObject, pyqtSignal
from werkzeug.serving import make_server

from src.context import AppContext, Participant, Session

QUESTIONS_FOLDER = Path('questions')

class ServerAPI(Thread, QObject):
    on_start = pyqtSignal()
    on_session_created = pyqtSignal(Session)

    def __init__(self, host='0.0.0.0', port=5000):
        Thread.__init__(self)
        QObject.__init__(self)
        self.app = Flask(__name__, static_folder='../../../client/build')

        @self.app.route('/api/session/<int:session_id>', methods=['GET'])
        def api_session_handle_get(session_id: int):
            session = AppContext.sessions.get(session_id, None)
            if session is None:
                return "Session not found", 404

            return jsonify(session.as_dict)

        @self.app.route('/api/session', methods=['GET'])
        def api_get_all_sessions():
            return jsonify([session.as_dict for session in AppContext.sessions.values()])

        @self.app.route('/api/session', methods=['POST'])
        def api_create_session():
            session = Session()
            AppContext.sessions[session.id] = session

            self.on_session_created.emit(session)
            return jsonify(session.as_dict)

        @self.app.route('/api/session/<int:session_id>', methods=['POST'])
        def api_edit_session(session_id: int):
            session = AppContext.sessions.get(session_id, None)
            if session is None:
                return "Session not found", 404

            session_data = request.json
            if any(
                key not in ['status', 'question_id', 'duration']
                for key in session_data.keys()
            ):
                return "Invalid parameter", 400

            if 'status' in session_data:
                try:
                    session.status = Session.Status(session_data['status'])
                except ValueError:
                    return "Requested status is not valid", 400

            if 'question_id' in session_data:
                question_id = session_data['question_id']
                if not isinstance(question_id, int):
                    return "Requested question_id must be an integer", 400

                if not (QUESTIONS_FOLDER / str(question_id)).is_dir():
                    return "Requested question_id doesn't exist", 404

                session.active_question = question_id

            if 'duration' in session_data:
                if not isinstance(session_data['duration'], int):
                    return "Requested duration must be an integer", 400

                session.duration = session_data['duration']

            return jsonify(session.as_dict)

        @self.app.route('/api/session/<int:session_id>/participants', methods=['GET'])
        def api_session_get_all_participants(session_id: int):
            session = AppContext.sessions.get(session_id, None)
            if session is None:
                return "Session not found", 404

            return jsonify([participant.as_dict for participant in session.participants])

        @self.app.route('/api/session/<int:session_id>/participants', methods=['POST'])
        def api_session_add_participant(session_id: int):
            if 'user' not in request.json:
                return "Invalid request", 400
            username = request.json['user']

            session = AppContext.sessions.get(session_id, None)
            if session is None:
                return "Session not found", 404

            if any(username == participant.username for participant in session.participants.values()):
                return "Participant already joined session", 400

            participant = Participant(username)
            session.add_participant(participant)

            return jsonify(participant.as_dict)

        @self.app.route('/api/session/<int:session_id>/participants/<int:participant_id>', methods=['DELETE'])
        def api_session_remove_participant(session_id: int, participant_id: int):
            # TODO: Implement the participant delete endpoint
            return "Not implemented", 500

        @self.app.route('/api/question/<int:question_id>')
        def api_question_handle(question_id: int):
            question = AppContext.questions.get(question_id, None)
            if question is None:
                return "Question not found", 404

            return jsonify(question.as_dict)

        @self.app.route('/api/question/<int:question_id>/image')
        def api_question_image_handle(question_id: int):
            question = AppContext.questions.get(question_id, None)
            if question is None:
                return "Question not found", 404

            return send_file(question.img_path) if question.img_is_local else redirect(question.img_path)

        # Serve client app
        @self.app.route('/', defaults={'path': ''})
        @self.app.route('/<path:path>')
        def client_handler(path):
            if path == '' or not (Path(self.app.static_folder) / path).is_file():
                return send_from_directory(self.app.static_folder, 'index.html')

            return send_from_directory(self.app.static_folder, path)

        self.server = make_server(host, port, self.app, threaded=True)
        self.ctx = self.app.app_context()
        self.ctx.push()

    def run(self):
        self.on_start.emit()
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()
