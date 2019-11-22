import os
from app import app, APPLICATION_PORT

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=APPLICATION_PORT, threaded=True)
