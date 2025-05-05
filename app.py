from flask import Flask
from feedback import feedback_bp

app = Flask(__name__)
app.register_blueprint(feedback_bp)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
