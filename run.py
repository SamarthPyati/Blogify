from blogify import app

if __name__ == "__main__":
    app.app_context().push()
    app.run(debug=True, port=9001)             # can directly run the server with 'python3 main.py'
