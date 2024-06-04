from blogify import app
from blogify import db

if __name__ == "__main__":
    app.app_context().push()
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=9001)             # can directly run the server with 'python3 main.py'
