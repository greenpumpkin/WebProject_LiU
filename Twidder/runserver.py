from gevent.wsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler
from flask import Flask
from Twidder import app

app = Flask(__name__)

if __name__ == '__main__':
    server = WSGIServer(("", 5000), app, handler_class=WebSocketHandler)
    app.debug = True
    server.serve_forever()
    #database_helper.init_db(app)