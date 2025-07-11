from flask import Blueprint, render_template, send_file, Response, request, jsonify, flash, current_app, redirect, url_for, session, make_response
from flask_mail import Message
from model.extensions import mail, limiter, engine
import requests
import os
import csv 
import torch #
from transformers import DistilBertTokenizer, DistilBertModel #
from nltk.sentiment.vader import SentimentIntensityAnalyzer #
import re
from model.Login import Login
from model.User import User
from model.Utils import DatabaseError
from model.Database.AuditLogsTBL import AuditLogsTable
from model.Database.UsersTBL import UserTable
from model.Database.ArticlesTBL import ArticlesTable
from model.Database.ModelVersionsTBL import ModelVersionsTable
from model.Database.PredictedArticledTBL import PredictedArticlesTable
from model.Validation import Validation

from model.Validation import Validation
import json
from functools import wraps
from sqlalchemy import text
import pandas as pd
import zipfile
import io

from newspaper import Article # addd requiremnt and xml clean

main = Blueprint('main', __name__)





# Load the Sentiment Analyzer
analyzer = SentimentIntensityAnalyzer()

# ✅ Load Tokenizer
MODEL_NAME = "distilbert-base-uncased"
tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME)

# ✅ Load Device (CPU or GPU)
#device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
device = torch.device("cpu")

# ✅ Define Model (Same as Trained Model)
class FakeNewsClassifier(torch.nn.Module):
    def __init__(self, model_name, dropout=0.3):
        super().__init__()
        self.bert = DistilBertModel.from_pretrained(model_name)
        self.dropout = torch.nn.Dropout(dropout)
        self.fc = torch.nn.Linear(self.bert.config.hidden_size + 1, 2)  # +1 for sentiment intensity

    def forward(self, input_ids, attention_mask, intensities):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = self.dropout(outputs.last_hidden_state[:, 0, :])  # [CLS] token
        combined_features = torch.cat((pooled_output, intensities), dim=1)
        logits = self.fc(combined_features)
        return logits

# ✅ Load Model
model_path = "BERT_SA.pt"
#model_path = "/home/adrieleustaquio1/thesis/BERT_SA.pt"


model = FakeNewsClassifier(MODEL_NAME).to(device)
model.load_state_dict(torch.load(model_path, map_location=device))
model.eval()  # Set to evaluation mode

# ✅ Prediction Function
def predict(text, intensity=2):  # Default intensity = neutral (2)
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=128)
    input_ids = inputs["input_ids"].to(device)
    attention_mask = inputs["attention_mask"].to(device)

    # Convert Intensity to Tensor
    intensity_tensor = torch.tensor([[intensity]], dtype=torch.float32).to(device)

    # Run Model Inference
    with torch.no_grad():
        logits = model(input_ids, attention_mask, intensity_tensor)

    # Get Prediction & Confidence Score
    probabilities = torch.nn.functional.softmax(logits, dim=1)
    confidence, predicted_class = torch.max(probabilities, dim=1)

    prediction_value = round(confidence.item() * 100, 2)  # Confidence percentage
    description = "Fake" if predicted_class.item() == 0 else "Real"

    print(intensity)

    return prediction_value, description



@main.route('/prediction', methods=['POST'])
def prediction():
    text_orig = request.form.get('TEXT', '').strip()

    text = text_orig.lower()
    text = re.sub(r"http\S+|www\S+|@\w+|#\w+", "", text)
    text = re.sub(r"[^\w\s]", "", text) 
    text = re.sub(r"\d+", "<num>", text)
    text = re.sub(r"[^a-zA-Z\s<>]", "", text)

    prediction_value, description = predict(text)
    #return jsonify({'probability': prediction_value, 'description': description})
    # Sentiment Analysis
    sentiment_score = analyzer.polarity_scores(text)

    # Convert sentiment scores to percentages
    neg, neu, pos = sentiment_score['neg'], sentiment_score['neu'], sentiment_score['pos']
    total = neg + neu + pos
    neg_pct = round((neg / total) * 100, 2) if total > 0 else 0
    neu_pct = round((neu / total) * 100, 2) if total > 0 else 0
    pos_pct = round((pos / total) * 100, 2) if total > 0 else 0

    predictedTable=PredictedArticlesTable(engine)
    predictedTable.add_predicted_article(text_orig, 0 if description == "Fake" else 1)
    

    sentiment= {
            "negative": neg_pct,
            "neutral": neu_pct,
            "positive": pos_pct,
        }
    dominant_sentiment = max(sentiment, key=sentiment.get)

    someSentiment = [key for key, val in sentiment.items() if val > 0]

    if dominant_sentiment in someSentiment:
        someSentiment.remove(dominant_sentiment)

    if len(someSentiment) == 2:
        extraDesc = f"with some {someSentiment[0]} and {someSentiment[1]} elements."
    elif len(someSentiment) == 1:
        extraDesc = f"with some {someSentiment[0]} elements."
    else:
        extraDesc = "with no other sentiment elements."



    shortDescription=f"This article has been classified as {description}"+ f", with a confidence of {prediction_value}%." + f" The sentiment analysis shows the content is mostly {dominant_sentiment}, {extraDesc}"
    
    response = {
        "probability": prediction_value,
        "description": description,
        "shortDescription":shortDescription,
        "sentiment": {
            "negative": neg_pct,
            "neutral": neu_pct,
            "positive": pos_pct,
            "compound_score": sentiment_score['compound']
        }
    }



    print("Response:", response)  # Debugging
    return jsonify(response)

CSV_FILE = "data_articles.csv"
ARTICLES_PER_PAGE = 4  # Limit per page


# Function to read CSV and return data
def read_csv(page):
    articles = []
    
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            articles = list(reader)[::-1]  # Reverse order (newest first)

    # Calculate pagination
    start_idx = (page - 1) * ARTICLES_PER_PAGE
    end_idx = start_idx + ARTICLES_PER_PAGE
    paginated_articles = articles[start_idx:end_idx]

    total_pages = (len(articles) + ARTICLES_PER_PAGE - 1) // ARTICLES_PER_PAGE  # Calculate total pages

    return paginated_articles, total_pages


#UTILS
#DECORATOR RO PREVENT ACCESS DEPENDING ON ROLE OR LOGIN
def required(role="B"):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_data = session.get('user')

            if not user_data:
                return redirect(url_for('main.noaccess'))

            user = User.from_dict(json.loads(user_data)) 

            if role == 'A' and user.role != role:
                    return redirect(url_for('main.noaccess'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@main.app_context_processor # auto add item to jinja
def inject_user():
    user_data = session.get('user')
    if user_data:
        user = User.from_dict(json.loads(user_data))
        return dict(user=user)
    return dict(user=None)

@main.before_request
def clear_session_on_public_routes(): #✅
    public_routes = ['main.main_page', 'main.disclaimer', 'main.download', 'main.download-file', 'main.factcheck', 'main.contact','main.show_login_page','main.login']
    if request.endpoint in public_routes:
        session.pop('user', None)

def audit_log(action): # to audit log to db #✅
    user = session.get('user')
    user = User.from_dict(json.loads(user))

    audit=AuditLogsTable(engine)
    audit.add_audit_log(user.user_id, action)


#ADMIN ONLY ACCESS

@main.route('/noaccess') #✅
def noaccess():
    return render_template('noaccess.html')  


@main.route('/add_article', methods=['GET', 'POST']) #✅
@required()
def addarticle():
    if request.method == "POST":
        title = request.form.get('title')
        content = request.form.get('content')
        label = request.form.get('label')
        source = request.form.get('source')

        validate=Validation()

        result=validate.validate_title(title)
        if result is not True:
            return render_template('addarticle.html', error=result) # 150
        result=validate.validate_content(content)
        if result is not True:
            return render_template('addarticle.html', error=result) #40 to 500
        result=validate.validate_label_radio(label)
        if result is not True:
            return render_template('addarticle.html', error=result)
    
        user_data = session.get('user')
        user = User.from_dict(json.loads(user_data)) 

        if label=="R":
            label=1
        else:
            label=0


        articleTable=ArticlesTable(engine)
        articleTable.add_article(title,content,label,source.strip(),user.user_id)
        
        audit_log("Added a Article")
        
        return render_template('addarticle.html', success="Article submitted successfully!")

    else:
        return render_template('addarticle.html')


@main.route('/manage_user') #✅
@required('A')
def manageuser():

    error = request.args.get('error')
    success = request.args.get('success')
    print(error)

    userTBl=UserTable(engine)
    
    #allUsers= userTBl.get_users()

    page = request.args.get('page', 1, type=int)
    per_page = 10 
    offset = (page - 1) * per_page

    allUsers, total_items = userTBl.get_users(offset, per_page)

    total_pages = (total_items + per_page - 1) // per_page

    return render_template('manageuser1.html', error=error, success=success, items=allUsers, page=page, total_pages=total_pages, url="main.manageuser")

@main.route('/search_user') #✅
@required('A')
def searchuser():
    search = request.args.get('search1', '').strip()
    filter_value = request.args.get('filter', '').strip()

    userTBl=UserTable(engine)

    page = request.args.get('page', 1, type=int)
    per_page = 10 
    offset = (page - 1) * per_page

    if filter_value:
        allUsers, total_items = userTBl.search_users_with_filter(search, filter_value, offset, per_page)
    elif search:
        allUsers, total_items = userTBl.search_users(search, offset, per_page)
    else:
        allUsers = []
        total_items = 0

    total_pages = (total_items + per_page - 1) // per_page

    return render_template('manageuser1.html', search=search, items=allUsers, page=page, total_pages=total_pages, url="main.searchuser")

@main.route('/action_user', methods=["POST"]) #✅
@required('A')
def actionuser():
    action = request.form.get('action')
    user_id = request.form.get('user_id')

    userTBl=UserTable(engine)
    
    if action == 'remove':
        delete_user=userTBl.delete_user(user_id)

        if delete_user:
             audit_log("Deleted a User")
             return redirect(url_for('main.manageuser', error="User was Deleted!"))
        else:
            return redirect(url_for('main.manageuser', error="Admin can't be Deleted!"))

    elif action == 'update':
        return redirect(url_for('main.update_user', user_id=user_id))
 
@main.route('/create_user', methods=["GET", "POST"]) #✅
@required('A')
def createuser():
    if request.method == "POST":
        username = request.form.get('username')
        firstname = request.form.get('fname')
        lastname = request.form.get('lname')
        email = request.form.get('email')
        password = request.form.get('password')
        confpassword = request.form.get('confirm-password')
        role = request.form.get('role')

        validate=Validation()

        result=validate.validate_username(username)
        if result is not True:
            return render_template('createuser1.html', error=result)
        result=validate.validate_firstname(firstname)
        if result is not True:
            return render_template('createuser1.html', error=result)
        result=validate.validate_lastname(lastname)
        if result is not True:
            return render_template('createuser1.html', error=result)
        result=validate.validate_email(email)
        if result is not True:
            return render_template('createuser1.html', error=result)
        result=validate.validate_password(password)
        if result is not True:
            return render_template('createuser1.html', error=result)
        result=validate.validate_confirm_password(password, confpassword)
        if result is not True:
            return render_template('createuser1.html', error=result)
        result=validate.validate_role(role)
        if result is not True:
            return render_template('createuser1.html', error=result)
        
        userTable=UserTable(engine)
        userTable.add_user(username,firstname, lastname, email, password, role)
        
        audit_log("Added a User")
        
        return render_template('createuser1.html', success="User successfully created!")
    else:
        return render_template('createuser1.html')
    

@main.route('/update_user', methods=["GET", "POST"]) #✅
@required('A')
def update_user():
    if request.method == "POST":
        user_id = request.form.get('user-id')

        firstname = request.form.get('fname')
        lastname = request.form.get('lname')
        email = request.form.get('email')
        password = request.form.get('password')
        confpassword = request.form.get('confirm-password')
        change_password = request.form.get("change_password")
        role = request.form.get('role')
        enabled = request.form.get('status')

        validate=Validation()

        userTable=UserTable(engine)
        update_user=userTable.get_user_by_id(user_id)

        updates = {}
    
        if (firstname != update_user.first_name):
            result=validate.validate_firstname(firstname)
            if result is not True:
                return render_template('updateuser.html',user=update_user, error=result)
            updates["first_name"] = firstname
        
        if (lastname != update_user.last_name):
            result=validate.validate_lastname(lastname)
            if result is not True:
                return render_template('updateuser.html',user=update_user, error=result)
            updates["last_name"] = lastname

        if (email != update_user.email):    
            result=validate.validate_email(email)
            if result is not True:
                return render_template('updateuser.html',user=update_user, error=result)
            updates["email"] = email

        if (role != update_user.role):    
            result=validate.validate_role(role)
            if result is not True:
                return render_template('updateuser.html',user=update_user, error=result)
            updates["role"] = role
        
        if (int(enabled) != update_user.enabled):    
            result=validate.validate_enabled(enabled)
            if result is not True:
                return render_template('updateuser.html',user=update_user, error=result)
            updates["enabled"] = enabled

        if change_password == "1": 
            result=validate.validate_password(password)
            if result is not True:
                return render_template('updateuser.html',user=update_user, error=result)
            result=validate.validate_confirm_password(password, confpassword)
            if result is not True:
                return render_template('updateuser.html',user=update_user, error=result)
            
            updates["password_hash"] = password


        user_data = session.get('user')
        user = User.from_dict(json.loads(user_data)) 


        if  updates:
            userTable.update_user(user_id, user.user_id, **updates)
            update_user=userTable.get_user_by_id(user_id)
            audit_log("Updated a User")
            return render_template('updateuser.html', user=update_user, success="User was Successfully Updated!")
          
        return render_template('updateuser.html', user=update_user)
    else:
        user_id = request.args.get('user_id')

        userTable=UserTable(engine)
        update_user=userTable.get_user_by_id(user_id)
  
        return render_template('updateuser.html', user=update_user)

@main.route('/manage_audit') #✅
@required('A')
def manageaudit():
    audit=AuditLogsTable(engine)

    page = request.args.get('page', 1, type=int)
    per_page = 10 
    offset = (page - 1) * per_page

    allAudits, total_items = audit.get_audits(offset, per_page)

    total_pages = (total_items + per_page - 1) // per_page

    return render_template('manageaudit.html', items=allAudits, page=page, total_pages=total_pages, url="main.manageaudit")


@main.route('/search_audit') #✅
@required('A')
def searchaudit():
    search = request.args.get('search1', '').strip()

    audit=AuditLogsTable(engine)

    page = request.args.get('page', 1, type=int)
    per_page = 10 
    offset = (page - 1) * per_page

    if search:
        allAudits, total_items = audit.search_audits(search, offset, per_page)
    else:
        allAudits = []
        total_items = 0

    total_pages = (total_items + per_page - 1) // per_page

    return render_template('manageaudit.html', search=search, items=allAudits, page=page, total_pages=total_pages, url="main.searchaudit")


@main.route('/manage_articles') #✅
@required('A')
def managearticle():
        articles=ArticlesTable(engine)

        page = request.args.get('page', 1, type=int)
        per_page = 10 
        offset = (page - 1) * per_page

        allArticles, total_items = articles.get_articles(offset, per_page)

        total_pages = (total_items + per_page - 1) // per_page

        return render_template('managearticle.html', items=allArticles, page=page, total_pages=total_pages, url="main.managearticle")

@main.route('/search_article') #✅
@required('A')
def searcharticle():
    search = request.args.get('search1', '').strip()

    articles=ArticlesTable(engine)

    page = request.args.get('page', 1, type=int)
    per_page = 10 
    offset = (page - 1) * per_page

   
    if search:
        allArticle, total_items = articles.search_articles(search, offset, per_page)
    else:
        allArticle = []
        total_items = 0

    total_pages = (total_items + per_page - 1) // per_page

    return render_template('managearticle.html', search=search, items=allArticle, page=page, total_pages=total_pages, url="main.searcharticle")


@main.route('/update_article',  methods=["GET", "POST"]) #✅
@required('A')
def updatearticle():
    if request.method == "POST":
        article_id = request.form.get('article_id')

        title = request.form.get('title')
        content = request.form.get('content')
        label = request.form.get('label')
        source = request.form.get('source')

        source = source.strip() or None 

        status = request.form.get('status')

        articleTable=ArticlesTable(engine)
        update_article=articleTable.get_article_by_id(article_id)

        validate=Validation()

        updates = {}

        if (title != update_article.title):
            result=validate.validate_title(title)
            if result is not True:
                return render_template('updatearticle.html', error=result, article=update_article) # 150
            updates["title"] = title

        if (content != update_article.article_text):
            result=validate.validate_content(content)
            if result is not True:
                return render_template('updatearticle.html', error=result, article=update_article) #40 to 500
            updates["article_text"] = content
        

        if label=="R":
            label=1
        else:
            label=0


        if (label != update_article.label):    
            result=validate.validate_label(label)
            if result is not True:
                return render_template('updatearticle.html', error=result, article=update_article)
            updates["label"] = label

        if (source != update_article.sources):   
            updates["sources"] = source 

  
        if (status != update_article.status):   
            updates["status"] = status 
    
        user_data = session.get('user')
        user = User.from_dict(json.loads(user_data)) 

        print(updates)

        if  updates:
            articleTable.update_article(article_id, user.user_id, **updates)
            update_article=articleTable.get_article_by_id(article_id)
            audit_log("Updated a Article")
            return render_template('updatearticle.html', article=update_article, success="Article was Successfully Updated!")
        
        return render_template('updatearticle.html', article=update_article)


    else:
        article_id = request.args.get('article_id')

        articles=ArticlesTable(engine)
        update_article=articles.get_article_by_id(article_id)

        return render_template('updatearticle.html', article=update_article)

@main.route('/manage_models') #✅
@required('A')
def managemodels():
    models=ModelVersionsTable(engine)

    page = request.args.get('page', 1, type=int)
    per_page = 10 
    offset = (page - 1) * per_page

    allModels, total_items = models.get_models(offset, per_page)

    total_pages = (total_items + per_page - 1) // per_page

    return render_template('managemodel.html', items=allModels, page=page, total_pages=total_pages, url="main.managemodels")


@main.route('/toggle_model', methods=["POST"]) #✅
@required('A')
def togglemodel():
    model_id = request.form.get('model_id')
    
    models=ModelVersionsTable(engine)

    models.toggle_model(model_id)

    return redirect(url_for('main.managemodels'))  


#COLLABORATOR AND ADMIN ACCESS
#show login page only
@main.route('/login', methods=['GET']) #✅
def show_login_page():
    return render_template('admin.html')


@main.route('/logout') #✅
def logout():
    audit_log("Logged out")

    session.pop('user', None)  
    flash("You have been logged out.", "info")
    return redirect(url_for('main.main_page'))  


@main.route('/login', methods=['POST'])  #✅
def login():
    error = None  # Default to None, so it's not always displayed

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            login=Login(username,password,engine)
            if login.validate_credentials():
                user = login.get_user()

                if (user.enabled==0):
                    error="User is Disabled"
                    return render_template('admin.html', error=error)

                #establish a user sessions
                session['user'] = json.dumps(user.to_dict())

                audit_log("Logged in")

                return redirect(url_for('main.addarticle'))
            else:
                error = "Invalid credentials"

        except DatabaseError as e:
             return render_template(
                'genericError.html',
                title="Database Error",
                header="Database Error",
                description=str(e)
            )
    return render_template('admin.html', error=error)  # Pass None if no error




#ALL CAN ACCESs

@main.route('/') #✅
@main.route('/home')
def main_page():
    return render_template('index1.html', recaptcha_site_key=current_app.config.get("RECAPTCHA_SITE_KEY"))

@main.route('/disclaimer') #✅
def disclaimer():
    return render_template('disclaimer.html')

@main.route('/download') #✅
def download():
    return render_template('download2.html')

@main.route('/download-file') #✅
def download_file():

    articleTBL=ArticlesTable(engine)
    allArticles=articleTBL.get_all_approved_articles()


    data = [vars(article) for article in allArticles]  #


    for d in data:
        d.pop('_sa_instance_state', None)

    selected_columns = ['article_text', 'label']
    df1 = pd.DataFrame(data)[selected_columns]

    df2 = pd.read_csv("fake_news_results.csv", usecols=[0, 1])
    df2.columns = ['article_text', 'label']

    

    combined_df = pd.concat([df1, df2], ignore_index=True)

    csv_buffer = io.StringIO()
    combined_df.to_csv(csv_buffer, index=False)
    csv_bytes = io.BytesIO(csv_buffer.getvalue().encode('utf-8'))


    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr("fake_news_results.csv", csv_bytes.getvalue())

    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='fake_news_results.zip'
    )

@main.route('/how-to-use') #✅
def howtouse():
    return render_template('howtouse.html')


 
@main.route('/factcheck') #✅
def factcheck():

    articles=ArticlesTable(engine)

    page = request.args.get('page', 1, type=int)
    per_page = 10 
    offset = (page - 1) * per_page

    allArticles, total_items = articles.get_approved_articles(offset, per_page)

    total_pages = (total_items + per_page - 1) // per_page

    print(allArticles)

    return render_template('factcheck.html', items=allArticles, page=page, total_pages=total_pages, url="main.factcheck")


@main.route('/extract_text', methods=['POST'])
def extract_text():
    url = request.form.get('article_url')

    if not url:
        return jsonify({'error': 'No URL provided', 'details': 'article_url is missing or empty'}), 400

    try:
        article = Article(url)
        article.download()
        article.parse()

        title = article.title or ''
        text = article.text or ''

        print("RESULT")
        print("Title:", title)
        print("Text:", text[:100])  # Print preview only

        return jsonify({
            'headline': title,
            'content': text
        })

    except Exception as e:
        print("Exception:", e)
        return jsonify({'error': 'Failed to extract content', 'details': str(e)}), 500



@main.route('/contact', methods=['POST'])  #❌ fix captcha
@limiter.limit("10 per day")
def contact():
    user_fname = request.form.get('fname')
    user_lname = request.form.get('lname')
    user_email = request.form.get('email')
    user_subj = request.form.get('subject')
    user_msg = request.form.get('message')

    validate=Validation()
    result=validate.validate_username(user_fname)
    if result is not True:
        print("<script type='text/javascript'>alert('Please fill all required fields!');</script>")



    recaptcha_response = request.form.get("g-recaptcha-response")
    secret_key = current_app.config.get("RECAPTCHA_SECRET_KEY")
    
    verify_url = "https://www.google.com/recaptcha/api/siteverify"
    payload = {
        "secret": secret_key,
        "response": recaptcha_response,
        "remoteip": request.remote_addr,
    }
    r = requests.post(verify_url, data=payload)
    result = r.json()

    print("reCAPTCHA verification:", result)

    if result.get("success"):
        msg = Message(
            subject=user_subj,
            sender=user_email,
            recipients=["csthesis8@gmail.com"],
            body=f"""
            New Contact Form Submission:

            Name: {user_fname} {user_lname}
            Email: {user_email}

            Message:
            {user_msg}
            """
        )

        try:
            mail.send(msg)
            flash("Email sent successfully!", "success")
        except Exception as e:
            flash(f"Error sending email: {str(e)}", "danger")

    else:
        flash("reCAPTCHA verification failed. Please try again.", "danger")

    return redirect(url_for("main.main_page"))

