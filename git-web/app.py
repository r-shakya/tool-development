from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import json

app = Flask(__name__)
app.secret_key = "rs"

app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///todo.db"
app.config['SQLALCHEMY_BINDS']={"auth":"sqlite:///auth.db", "feedback":"sqlite:///feedback.db"}
        
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db = SQLAlchemy(app)

#database for storing list of issues in users todo-list
class Todo(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"{self.sno} - {self.user} - {self.title}"

#database for authentication of users
class Auth(db.Model):
    __bind_key__="auth"
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(500), nullable=False)
    password = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"{self.sno} - {self.name} - {self.email} - {self.password}"

#database for getting feedback from the user  --- not yet implement
class Feedback(db.Model):
    __bind_key__="feedback"
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

#default route for website
@app.route('/', methods=['GET','POST'])
def index():
    user="none"
    if 'email' in session:
        user = session['email']

    #retrive data for training classifier
    f = open('static/real_data.json','r')
    train = json.load(f)
    f.close()
    print(len(train["labels"]))

    #training classifer --- start
    from sklearn.feature_extraction.text import CountVectorizer
    count_vect=CountVectorizer()
    X_train_tf=count_vect.fit_transform(train["titles"])
    print(X_train_tf.shape)

    from sklearn.feature_extraction.text import TfidfTransformer
    tfidf_transformer = TfidfTransformer()
    X_train_tfidf=tfidf_transformer.fit_transform(X_train_tf)
    print(X_train_tfidf.shape)

    from sklearn.naive_bayes import MultinomialNB
    clf = MultinomialNB().fit(X_train_tfidf, train["labels"])
    print("we are ready to predict")
    #training classifier --- end

    #retrive tensorflow open issues for default output
    f = open('static/tensorflow_opened_issues.json','r')
    issues_list = json.load(f)
    f.close()
    print("data received",len(issues_list))

    
    #retrieve the open issues from git-api by owner and repo name --- start
    if request.method=="POST":
        issues_list=[]
        username = request.form['owner']
        repo = request.form['repo']

        url=f"https://api.github.com/repos/{username}/{repo}/issues"
        pageno=1
        res=100
        while(res==100):
            params = {
                "state": "open",
                "per_page": "100",
                "page":pageno,
            }
            headers = {

            }
            response = requests.get(url,headers=headers, params=params)
            issues_list=issues_list+response.json()
            res=len(response.json())
            print(response,pageno)
            pageno=pageno+1
            break
    #retrieve the open issues from git-api by owner and repo name --- start

    #collect issues labels, titiles and urls ----   start
    labels_list=[]
    issues_titles=[]
    issues_url=[]

    for i in range(len(issues_list)):
        issues_titles=issues_titles+[issues_list[i]["title"]];
        issues_url=issues_url+[issues_list[i]["html_url"]];
        
        issue_labels_list = issues_list[i]["labels"]
        single_label_list=[]
        
        for j in range(len(issue_labels_list)):
            single_label_list=single_label_list+[issue_labels_list[j]["name"]]
        labels_list=labels_list+[single_label_list]
    #collect issues labels, titiles and urls ----   end


    print("got the titles for prediction",len(issues_titles))
    print("got the labels for prediction",len(labels_list))

    real_cat = [0,0,0,0,0,0] #will count how many labeled issues in each class
    pred_cat = [0,0,0,0,0,0] #will count how many unlabeled issues in each class


    #prediction for unlabeled issues --- start
    import re

    issue_type=[] #will store type of the issues means label
    issue_num=[] #will store respective num value of that class or label
        
    predicted_issues=0
    non_predicted_issues=0
        
    labeled_issues=[] #will store labeled issues titles
    labeled_issues_num=[] #will store labeled issues class

    for i in range(len(labels_list)):
        lb=labels_list[i]
        l=len(lb)
            
        if(l>0):
            itr=0
            for j in range(len(lb)):
                if(re.search("docs-bug", lb[j]) or re.search("documentation", lb[j])):
                    issue_type=issue_type+[['docs-bug']]
                    issue_num=issue_num+[0]
                    real_cat[0]=real_cat[0]+1
                    non_predicted_issues=non_predicted_issues+1
                    labeled_issues=labeled_issues+[issues_titles[i]]
                    labeled_issues_num=labeled_issues_num+[0]
                    break
                elif(re.search("bug", lb[j])):
                    issue_type=issue_type+[['bug']]
                    issue_num=issue_num+[1]
                    real_cat[1]=real_cat[1]+1
                    non_predicted_issues=non_predicted_issues+1
                    labeled_issues=labeled_issues+[issues_titles[i]]
                    labeled_issues_num=labeled_issues_num+[1]
                    break
                elif(re.search("feature", lb[j]) or re.search("enhancement", lb[j])):
                    issue_type=issue_type+[['feature']]
                    issue_num=issue_num+[2]
                    real_cat[2]=real_cat[2]+1
                    non_predicted_issues=non_predicted_issues+1
                    labeled_issues=labeled_issues+[issues_titles[i]]
                    labeled_issues_num=labeled_issues_num+[2]
                    break
                elif(re.search("support", lb[j])):
                    issue_type=issue_type+[['support']]
                    issue_num=issue_num+[3]
                    real_cat[3]=real_cat[3]+1
                    non_predicted_issues=non_predicted_issues+1
                    labeled_issues=labeled_issues+[issues_titles[i]]
                    labeled_issues_num=labeled_issues_num+[3]
                    break
                elif(re.search("performance", lb[j])):
                    issue_type=issue_type+[['performance']]
                    issue_num=issue_num+[4]
                    real_cat[4]=real_cat[4]+1
                    non_predicted_issues=non_predicted_issues+1
                    labeled_issues=labeled_issues+[issues_titles[i]]
                    labeled_issues_num=labeled_issues_num+[4]
                    break
                elif(re.search("build/install", lb[j])):
                    issue_type=issue_type+[['build/install']]
                    issue_num=issue_num+[5]
                    real_cat[5]=real_cat[5]+1
                    non_predicted_issues=non_predicted_issues+1
                    labeled_issues=labeled_issues+[issues_titles[i]]
                    labeled_issues_num=labeled_issues_num+[5]
                    break
                itr=itr+1
            if(itr==l):
                #prediction of unrecognized issue
                issue_type=issue_type+[['unrecognized']] #keep it as unrecognized
                #transform test data
                X_test_tf=count_vect.transform([issues_titles[i]])
                X_test_tfidf=tfidf_transformer.transform(X_test_tf)
                predicted = clf.predict(X_test_tfidf)
                
                issue_num=issue_num+[predicted[0]]
                predicted_issues=predicted_issues+1
                pred_cat[predicted[0]]=pred_cat[predicted[0]]+1
        else:
            #prediction of unrecognized issue
            issue_type=issue_type+[['unrecognized']] #keep it as unrecognized
            #transform test data
            X_test_tf=count_vect.transform([issues_titles[i]])
            X_test_tfidf=tfidf_transformer.transform(X_test_tf)
            predicted = clf.predict(X_test_tfidf)
            
            issue_num=issue_num+[predicted[0]]
            predicted_issues=predicted_issues+1
            pred_cat[predicted[0]]=pred_cat[predicted[0]]+1
    print(len(issue_type))
    print(len(issue_num))
    print("prediction complete")
    #prediction for unlabeled issues --- end


    #prediction for labeled issues for checking accuracy --- start
    predicted_num=[]
    for i in range(len(labeled_issues)):
        #transform test data
        X_test_tf=count_vect.transform([labeled_issues[i]])
        X_test_tfidf=tfidf_transformer.transform(X_test_tf)
        predicted = clf.predict(X_test_tfidf)
            
        predicted_num=predicted_num+[predicted[0]]
    print(len(predicted_num))
    print("prediction complete for labeled issues")
    #prediction for labeled issues for checking accuracy --- end

    #check the accuracy --- if predicted and real label match
    count=0
    for i in range(len(labeled_issues)):
        if(labeled_issues_num[i]==predicted_num[i]):
            count=count+1
    print(count,len(predicted_num))
    l_count=len(predicted_num)-count
    
    #prioritization of issues by giving them weightage --- start
    w=[]
    #give the weight based on their class means labels
    for i in range(len(issue_num)):
        if(issue_num[i]==0):
            w=w+[0.2]
        elif(issue_num[i]==1):
            w=w+[0.5]
        elif(issue_num[i]==2):
            w=w+[0.4]
        elif(issue_num[i]==3):
            w=w+[0.0]
        elif(issue_num[i]==4):
            w=w+[0.1]
        elif(issue_num[i]==5):
            w=w+[0.3]
    print(len(issue_num),len(w))
    print("init prioritization")

    #increase weight based on comment
    for i in range(len(issue_num)):
        w[i]=w[i]+0.01*issues_list[i]["comments"]
    print(len(issue_num),len(w))
    print("increase weights based on number of comments")

    #increased weight based on author_association
    for i in range(len(issue_num)):
        if(issues_list[i]["author_association"]=="OWNER"):
            w[i]=w[i]+0.004
        elif(issues_list[i]["author_association"]=="MEMBER"):
            w[i]=w[i]+0.003
        elif(issues_list[i]["author_association"]=="COLLABORATOR"):
            w[i]=w[i]+0.002
        elif(issues_list[i]["author_association"]=="CONTRIBUTOR"):
            w[i]=w[i]+0.001
    print(len(issue_num),len(w))
    print("increase weights on author association")

    #increased weight if the issue is not assigned to anyone yet
    for i in range(len(issue_num)):
        if(len(issues_list[i]["assignees"])==0):
             w[i]=w[i]+0.0001
    print(len(issue_num),len(w))
    print("increase weights based on assigness")
    #prioritization of issues by giving them weightage --- start

    #sort all the issues by their weightage in descending order --- start    
    import pandas as pd
    
    mydataset = {
        'title': issues_titles,
        'urls': issues_url,
        'type': issue_num,
        'weight': w
    }
        
    myvar = pd.DataFrame(mydataset)

    myvar1=myvar.sort_values(by=['weight'], ascending=False)
    new1=[] #it will contain titles of issues
    new2=[] #it will contain urls of issues

    for i in range(len(myvar1)):
        new1=new1+[myvar1.iloc[i][0]]
        new2=new2+[myvar1.iloc[i][1]]
    print(len(new1),len(new2))
    print("final data")
    #sort all the issues by their weightage in descending order --- end

    error="none"
    if 'error' in session:
        error = session['error']
        session.pop('error',None)
    return render_template('index.html',issues_list=issues_list,new1=new1,new2=new2,count=count,l_count=l_count,p_i=predicted_issues,n_p_i=non_predicted_issues,user=user,error=error,real_cat=real_cat,pred_cat=pred_cat)

#route for adding issue in user todo list
@app.route('/add/<int:sno>', methods=['GET','POST'])
def add(sno):
    if 'email' in session:  
        email = session['email']
        if request.method=="GET":
            title = request.args.get("title")
            desc = request.args.get("desc")
            todo = Todo(user=email, title=title, desc=desc)
            db.session.add(todo)
            db.session.commit()
            print("issue added")
    else:
        print("login first")
        session['error']="login first"
    return redirect('/')

#route for signup
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method=="POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        user = Auth.query.filter_by(email=email).first()
        if (user):
            print("email is already in use: ",email)
            session['error']="email is already in use"
            return redirect('/')

        user = Auth(name=name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        print("user added: ",user)
        session['email']=email
        return redirect('/')

#route for login
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=="POST":
        email = request.form['email']
        password = request.form['password']

        user = Auth.query.filter_by(email=email).first()
        if(user):
            if (user.password == password):
                print("password matched: ",user)
                session['email']=email
            else:
                print("password not matched")
                session['error']="password not matched"
        else:
            print("user not found")
            session['error']="user not found"
        
        return redirect('/')

#route for logout
@app.route('/logout', methods=['GET','POST'])
def logout():
    if 'email' in session:  
        session.pop('email',None)
    return redirect('/')

#route for retreiving all the issues in users todo list and render it in list.html
@app.route('/list', methods=['GET','POST'])
def showlist():
    error="none"
    if 'email' in session:
        user = session['email']
        allTodo = Todo.query.filter_by(user=user).all()
        return render_template('list.html',allTodo=allTodo,user=user,error=error)
    session['error']="login first"
    return redirect('/')

#user can delete the issue from his list ---- either he resolve the issue or some other reason
@app.route('/delete/<int:sno>')
def delete(sno):
    if 'email' in session:
        user = session['email']
        todo = Todo.query.filter_by(sno=sno).first()
        db.session.delete(todo)
        db.session.commit()
        allTodo = Todo.query.filter_by(user=user).all()
        return render_template('list.html',allTodo=allTodo,user=user)
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True, port=5000)