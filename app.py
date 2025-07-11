from flask import Flask, render_template
from model.extensions  import mail, limiter
from controller.main import main
from werkzeug.middleware.proxy_fix import ProxyFix
import os
from dotenv import load_dotenv
load_dotenv()  

app = Flask(__name__)

# Apply ProxyFix 
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

#turn on DEBUGMODE
app.config["DEBUG"] = True

#app.secret_key = "your_random_secret_key"
app.secret_key = os.getenv("SECRET_KEY")  # Get secret key from .env

#RECAPTCHA
app.config['RECAPTCHA_SITE_KEY'] = os.getenv("RECAPTCHA_SITE_KEY")
app.config['RECAPTCHA_SECRET_KEY'] = os.getenv("RECAPTCHA_SECRET_KEY")


#MAIL-STP
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

#SQL - Delete
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

mail.init_app(app)
limiter.init_app(app)

app.register_blueprint(main)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404page.html'), 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  
    app.run(host="0.0.0.0", port=port, debug=True)
