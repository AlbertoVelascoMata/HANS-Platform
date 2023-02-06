import json
from pathlib import Path

class Question:
    last_id = 0

    @property
    def as_dict(self):
        return {
            'id': self.id,
            'query': self.query,
            'answers': self.answers,
        }

    def __init__(self, query, answers, img_path):
        Question.last_id += 1
        self.id = Question.last_id
        self.query = query
        self.answers = answers
        self.img_path = img_path

    @staticmethod
    def from_folder(question_folder: Path):
        info_path = question_folder / 'info.json'
        img_path = next((
                f
                for f in question_folder.glob('img.*')
                if f.suffix in ['.png', '.tif']
            ), None)
        if not info_path.is_file() or not img_path:
            return None

        with open(info_path, 'r') as f:
            data = json.load(f)

        return Question(
            query=data.get('question', None),
            answers=data.get('answers', None),
            img_path=img_path
        )
