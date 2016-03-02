from gevent.wsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler
from Twidder import app

server = WSGIServer(("", 5000), app, handler_class=WebSocketHandler)
app.debug = True
server.serve_forever()
#database_helper.init_db(app)