from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///todo.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db = SQLAlchemy(app)

class Todo(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"{self.sno} - {self.title}"

@app.route('/', methods=['GET','POST'])
def hello_world():

    f = open('static/real_data.json','r')
    train = json.load(f)
    f.close()
    print(len(train["labels"]))

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

    f = open('static/tensorflow_opened_issues.json','r')
    issues_list = json.load(f)
    f.close()
    print("data received",len(issues_list))

    new1=[]
    new2=[]
    if request.method=="POST":
        username = request.form['owner']
        repo = request.form['repo']
        url=f"https://api.github.com/repos/{username}/{repo}/issues"
        params = {
            "state": "open",
        }
        headers = {

        }
        response = requests.get(url,headers=headers, params=params)
        issues_list=response.json()
    
    data=[]
    labels_list=[]
    issues_url=[]
    for i in range(len(issues_list)):
        single_data=[]
        issue=issues_list[i]
        issue_title=issue["title"]
        issue_body=issue["body"]
        issues_url=issues_url+[issue["html_url"]]
        
        single_data=single_data+[issue_title,issue_body];
        
        data=data+[single_data];
        
        issue_labels_list = issue["labels"]
        single_label_list=[]
        
        for j in range(len(issue_labels_list)):
            label=issue_labels_list[j]
            label_name=label["name"]
            single_label_list=single_label_list+[label_name]
        labels_list=labels_list+[single_label_list]

    issues_titles=[]
    for i in range(len(data)):
        issues_titles=issues_titles+[data[i][0]]
    print("got the titles for prediction",len(issues_titles))
    print("got the labels for prediction",len(labels_list))

    real_cat0=0
    real_cat1=0
    real_cat2=0
    real_cat3=0
    real_cat4=0
    real_cat5=0

    import re
    issue_type=[]
    issue_num=[]
        
    predicted_issues=0
    non_predicted_issues=0
        
    #for analysis purpose
    labeled_issues=[]
    labeled_issues_num=[]
    for i in range(len(labels_list)):
        lb=labels_list[i]
        l=len(lb)
            
        if(l>0):
            itr=0
            for j in range(len(lb)):
                if(re.search("docs-bug", lb[j])):
                    issue_type=issue_type+[['docs-bug']]
                    issue_num=issue_num+[0]
                    real_cat0=real_cat0+1
                    non_predicted_issues=non_predicted_issues+1
                    labeled_issues=labeled_issues+[issues_titles[i]]
                    labeled_issues_num=labeled_issues_num+[0]
                    break
                elif(re.search("bug", lb[j])):
                    issue_type=issue_type+[['bug']]
                    issue_num=issue_num+[1]
                    real_cat1=real_cat1+1
                    non_predicted_issues=non_predicted_issues+1
                    labeled_issues=labeled_issues+[issues_titles[i]]
                    labeled_issues_num=labeled_issues_num+[1]
                    break
                elif(re.search("feature", lb[j])):
                    issue_type=issue_type+[['feature']]
                    issue_num=issue_num+[2]
                    real_cat2=real_cat2+1
                    non_predicted_issues=non_predicted_issues+1
                    labeled_issues=labeled_issues+[issues_titles[i]]
                    labeled_issues_num=labeled_issues_num+[2]
                    break
                elif(re.search("support", lb[j])):
                    issue_type=issue_type+[['support']]
                    issue_num=issue_num+[3]
                    real_cat3=real_cat3+1
                    non_predicted_issues=non_predicted_issues+1
                    labeled_issues=labeled_issues+[issues_titles[i]]
                    labeled_issues_num=labeled_issues_num+[3]
                    break
                elif(re.search("performance", lb[j])):
                    issue_type=issue_type+[['performance']]
                    issue_num=issue_num+[4]
                    real_cat4=real_cat4+1
                    non_predicted_issues=non_predicted_issues+1
                    labeled_issues=labeled_issues+[issues_titles[i]]
                    labeled_issues_num=labeled_issues_num+[4]
                    break
                elif(re.search("build/install", lb[j])):
                    issue_type=issue_type+[['build/install']]
                    issue_num=issue_num+[5]
                    real_cat5=real_cat5+1
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
        else:
            #prediction of unrecognized issue
            issue_type=issue_type+[['unrecognized']] #keep it as unrecognized
            #transform test data
            X_test_tf=count_vect.transform([issues_titles[i]])
            X_test_tfidf=tfidf_transformer.transform(X_test_tf)
            predicted = clf.predict(X_test_tfidf)
            
            issue_num=issue_num+[predicted[0]]
            predicted_issues=predicted_issues+1
    print(len(issue_type))
    print(len(issue_num))
    print("prediction complete")


    #prediction for labeled issues
    predicted_num=[]
    for i in range(len(labeled_issues)):
        #transform test data
        X_test_tf=count_vect.transform([labeled_issues[i]])
        X_test_tfidf=tfidf_transformer.transform(X_test_tf)
        predicted = clf.predict(X_test_tfidf)
            
        predicted_num=predicted_num+[predicted[0]]
    print(len(predicted_num))
    print("prediction complete for labeled issues")

    count=0
    for i in range(len(labeled_issues)):
        if(labeled_issues_num[i]==predicted_num[i]):
            count=count+1
    print(count,len(predicted_num))
    l_count=len(predicted_num)-count

    w=[]
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

    for i in range(len(issue_num)):
        w[i]=w[i]+0.01*issues_list[i]["comments"]
    print(len(issue_num),len(w))
    print("increase weights based on number of comments")

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

    for i in range(len(issue_num)):
        if(len(issues_list[i]["assignees"])==0):
             w[i]=w[i]+0.0001
    print(len(issue_num),len(w))
    print("increase weights based on assigness")


    list_of_issues_titles=issues_titles
    list_of_issues_types=issue_num
    list_of_issues_weights=w
    list_of_issues_url=issues_url
        
    import pandas as pd
        
    mydataset = {
        'title': list_of_issues_titles,
        'urls': list_of_issues_url,
        'type': list_of_issues_types,
        'weight': list_of_issues_weights
    }
        
    myvar = pd.DataFrame(mydataset)

    myvar1=myvar.sort_values(by=['weight'], ascending=False)
    new1=[]
    new2=[]
    for i in range(len(myvar1)):
        new1=new1+[myvar1.iloc[i][0]]
        new2=new2+[myvar1.iloc[i][1]]
    print(len(new1),len(new2))
    print("final data")
    
    return render_template('index.html',issues_list=issues_list,new1=new1,new2=new2,count=count,l_count=l_count,p_i=predicted_issues,n_p_i=non_predicted_issues)

@app.route('/add/<int:sno>', methods=['GET','POST'])
def add(sno):
    if request.method=="GET":
        title = request.args.get("title")
        desc = request.args.get("desc")
        todo = Todo(title=title, desc=desc)
        db.session.add(todo)
        db.session.commit()
    return redirect('/')

@app.route('/list', methods=['GET','POST'])
def showlist():
    allTodo = Todo.query.all()
    return render_template('list.html',allTodo=allTodo)

@app.route('/show')
def products():
    allTodo = Todo.query.all()
    print(allTodo)
    return 'this is products page'

@app.route('/delete/<int:sno>')
def delete(sno):
    todo = Todo.query.filter_by(sno=sno).first()
    db.session.delete(todo)
    db.session.commit()
    return redirect('/')

@app.route('/update/<int:sno>', methods=['GET','POST'])
def update(sno):
    if request.method=="POST":
        title = request.form['title']
        desc = request.form['desc']
        todo = Todo.query.filter_by(sno=sno).first()
        todo.title=title
        todo.desc=desc
        db.session.add(todo)
        db.session.commit()
        return redirect('/')
    todo = Todo.query.filter_by(sno=sno).first()
    return render_template('update.html',todo=todo)

if __name__ == "__main__":
    app.run(debug=True, port=8000)