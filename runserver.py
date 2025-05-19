from os import environ
from __init__ import app

if __name__ == '__main__':
    try:
        PORT = int(environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(host="0.0.0.0", port=PORT)
