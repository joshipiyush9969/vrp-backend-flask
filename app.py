from flask import Flask
import logging
from random import randint

app = Flask(__name__)
check = randint(0, 255)
 
@app.route('/')
def hello_world():
    return f'Major OMG from: {check}' 
 
# main driver function
if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', true))

if __name__ != '__main__':
	# For logging in prod
    gunicorn_error_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_error_logger.handlers
    app.logger.setLevel(gunicorn_error_logger.level)
