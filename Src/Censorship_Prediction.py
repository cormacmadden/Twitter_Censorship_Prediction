import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt
import string
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.utils import shuffle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.dummy import DummyClassifier
from sklearn.metrics import roc_curve
from wordcloud import WordCloud, STOPWORDS

def run():
    fileDir = os.path.dirname(__file__)
    mypath = os.path.join(fileDir)

    #Import Censored Data
    censored_df=pd.read_csv(os.path.join(mypath, 'censored_tweets.csv'))
    censored_df = pd.DataFrame(censored_df)
    censored_df.insert(loc=3, column='y', value=0)
    censored_df = censored_df.drop(['id','lang'],axis=1)

    #import regular tweets
    uncensored_df=pd.read_csv(os.path.join(mypath, 'regular_tweets.csv'))
    uncensored_df = pd.DataFrame(uncensored_df)
    uncensored_df.insert(loc=3, column='y', value=1)
    uncensored_df = uncensored_df.drop(['id','lang'],axis=1)

    #merge and shuffle
    df = pd.concat([censored_df, uncensored_df], ignore_index=True, sort=False, )
    df = shuffle(df)
    df_x=df["text"]
    df_y=df["y"]

    plot_cloud(' '.join(censored_df["text"]))

    x_train, x_test, y_train, y_test = train_test_split(df_x, df_y, test_size=0.2, random_state=4)

    cv = CountVectorizer(min_df=2, max_df=90, lowercase='True', encoding="utf-8",ngram_range=(1, 1), stop_words = ["https"])

    tfidV = TfidfVectorizer(min_df=2, max_df=90, lowercase='True', encoding="utf-8",ngram_range=(1, 1), stop_words = ["https"])

    x_train_fit=cv.fit_transform(x_train)
    x_test_fit=cv.transform(x_test)
    test = x_train_fit.sum(axis=1)

    log_reg = LogisticRegression(C=5)
    mnb = MultinomialNB(alpha=2)
    kNN = KNeighborsClassifier(n_neighbors=20)
    log_reg.fit(x_train_fit,y_train)
    kNN.fit(x_train_fit,y_train)
    mnb.fit(x_train_fit,y_train)

    class_labels=mnb.classes_
    print_top10(cv, log_reg, class_labels)
    #important_features(cv,mnb,n=20)

    print("Accuracy: ", log_reg.score(x_test_fit, y_test))
    print("Accuracy: ", kNN.score(x_test_fit, y_test))
    print("Accuracy: ", mnb.score(x_test_fit, y_test))

    mnb_best_k(x_train_fit,y_train)
    best_min_diff(x_train,y_train)
    log_knn_dummy_ROC(x_train_fit,y_train,5,20,1)

def plot_cloud(words):
    wordcloud = WordCloud(width= 3000, height = 2000, random_state=1, colormap='Pastel1', collocations=False, stopwords = STOPWORDS)
    wordcloud.generate(words)   
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.margins(x=0, y=0)
    plt.show()

def knn_best_k(X,x_test_fit,y,y_test,title):
    fig = plt.figure()
    avg_accuracy=[]
    std_err=[]
    k_test = np.array(range(1,100,5))
    for k in k_test:
        knn = KNeighborsClassifier(n_neighbors=k)
        scores = cross_val_score(knn, X, y, scoring="accuracy")
        avg_accuracy.append(scores.mean())
        std_err.append(scores.std())

    plt.errorbar(k_test, avg_accuracy, yerr=std_err)
    plt.xlabel('k')
    plt.ylabel('Accuracy')
    plt.title('kNN (Censorship Model): Best k Value')
    plt.show()

def mnb_best_k(X,y):
    fig = plt.figure()
    avg_accuracy=[]
    std_err=[]
    alphas = np.array(range(0,15,1))
    for a in alphas:
        mnb = MultinomialNB(alpha=a)
        scores = cross_val_score(mnb, X, y, scoring="accuracy")
        avg_accuracy.append(scores.mean())
        std_err.append(scores.std())

    plt.errorbar(alphas, avg_accuracy, yerr=std_err)
    plt.xlabel('alpha')
    plt.ylabel('Accuracy')
    plt.title('MultinomialNB: Best alpha Value')
    plt.show()

def reg_best_c(X, y, title):
    fig = plt.figure()
    Cs = [0.001,0.01,0.05,0.1,0.25,0.5,1,1.5]

    avg_accuracy=[]
    std_err=[]
    for c in Cs:
        log_reg = LogisticRegression(C=c, max_iter=100)
        scores = cross_val_score(log_reg, X, y,cv=5, scoring="accuracy")
        avg_accuracy.append(scores.mean())
        std_err.append(scores.std())

    plt.errorbar(Cs, avg_accuracy, yerr=std_err,)
    plt.xlabel('C')
    plt.ylabel('Accuracy')
    plt.legend()

    plt.title(title)
    plt.legend(loc = 1)
    plt.show()
    return

def log_knn_dummy_ROC(X, y, c, k,a):
    fig = plt.figure()

    y_pred_log_reg =[]; y_pred_knn = []
    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    log_reg = LogisticRegression(C=c, solver = 'sag', max_iter=100)
    knn = KNeighborsClassifier(n_neighbors=k, algorithm='kd_tree')
    mnb = MultinomialNB(alpha=a)
    dummy = DummyClassifier(strategy="most_frequent")

    log_reg.fit(x_train, y_train)
    knn.fit(x_train, y_train)
    dummy.fit(x_train, y_train)
    mnb.fit(x_train, y_train)

    y_pred_log_reg = log_reg.predict(x_test)
    y_pred_knn = knn.predict(x_test)
    y_pred_dummy = dummy.predict(x_test)
    y_pred_mnb = mnb.predict(x_test)

    log_mat = confusion_matrix(y_test, y_pred_log_reg)
    mnb_mat = confusion_matrix(y_test, y_pred_mnb)
    knn_mat = confusion_matrix(y_test, y_pred_knn)
    dummy_mat = confusion_matrix(y_test, y_pred_dummy)

    print(classification_report(y_test, y_pred_log_reg, target_names=["Not-Censored", "Censored"]))
    print(classification_report(y_test, y_pred_mnb, target_names=["Not-Censored", "Censored"]))
    print(classification_report(y_test, y_pred_knn, target_names=["Not-Censored", "Censored"]))
    print(classification_report(y_test, y_pred_dummy, zero_division=0, target_names=["Not-Censored", "Censored"]))
    
    print("LogReg \n", log_mat)
    print("MultiNB \n", mnb_mat)
    print("Knn \n", knn_mat)
    print("Dummy \n", dummy_mat)

    scores = log_reg.predict_proba(x_test)
    fpr, tpr, _ = roc_curve(y_test, scores[:, 1])
    plt.plot(fpr, tpr)

    scores = mnb.predict_proba(x_test)
    fpr, tpr, _ = roc_curve(y_test, scores[:, 1])
    plt.plot(fpr, tpr)

    scores = knn.predict_proba(x_test)
    fpr, tpr, _ = roc_curve(y_test, scores[:, 1])
    plt.plot(fpr, tpr)

    scores = dummy.predict_proba(x_test)
    fpr, tpr, _ = roc_curve(y_test, scores[:, 1])
    plt.plot(fpr, tpr)

    plt.title('ROC Curves')
    plt.legend(['Logistic Regression','multi Nominal NB', 'K Nearest Neighbours', 'Dummy Classifier'])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.show()

def best_min_diff(X,y):
    
    fig = plt.figure()
    avg_accuracy=[]
    std_err=[]
    min_diffs= np.array(range(10,150,10))
    for m in min_diffs:
        cv = TfidfVectorizer(min_df=2, max_df=m,lowercase='True', encoding="utf-8",ngram_range=(1, 2))
        x_fit=cv.fit_transform(X)
        log_reg = LogisticRegression()
        scores = cross_val_score(log_reg, x_fit, y, scoring="accuracy")
        avg_accuracy.append(scores.mean())
        std_err.append(scores.std())

    plt.errorbar(min_diffs, avg_accuracy, yerr=std_err)
    plt.xlabel('max_diff')
    plt.ylabel('Accuracy')
    plt.title('cross validation of max_diff')
    plt.show()

def print_top10(vectorizer, clf, class_labels):
    """Prints features with the highest coefficient values, per class"""
    feature_names = vectorizer.get_feature_names()
    plot_cloud(' '.join(feature_names[:]))
    for class_label in enumerate(class_labels):
        top10 = np.argsort(clf.coef_[0][:])[-10:]
        print("%s: %s" % (class_label,
              " ".join(feature_names[j] for j in top10)))
            
def important_features(vectorizer,classifier,n=20):
    class_labels = classifier.classes_
    feature_names =vectorizer.get_feature_names()

    topn_class1 = sorted(zip(classifier.feature_count_[0], feature_names),reverse=True)[:n]
    topn_class2 = sorted(zip(classifier.feature_count_[1], feature_names),reverse=True)[:n]

    print("Important words in negative reviews")

    for coef, feat in topn_class1:
        print(class_labels[0], coef, feat)

    print("-----------------------------------------")
    print("Important words in positive reviews")

    for coef, feat in topn_class2:
        print(class_labels[1], coef, feat)
if __name__ == '__main__':
    run()

    '''
    featureNames = zip(cv.get_feature_names(), x_train_fit.sum(axis=1))
    #mostCommonWords = sorted(featureNames, key=lambda x:x[1],reverse = True)
    features = cv.vocabulary_
    #print(features)
    mostCommonWords = sorted(features.items(), key=lambda x:x[1],reverse = True)
    converted_dict = dict(mostCommonWords)
    #print(converted_dict)
    '''
    