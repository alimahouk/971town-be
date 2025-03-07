from flask import Flask
import os
from werkzeug.middleware.proxy_fix import ProxyFix


APP_ROOT = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config["PREFERRED_URL_SCHEME"] = "https"
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
#app.config["SERVER_NAME"] = "971.town"
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.wsgi_app = ProxyFix(app.wsgi_app)  # This fixes issues when running behind Nginx as a proxy.


from app import routes


if __name__ == "__main__":
    app.run(app,
            port=8000,
            threaded=True)
