import shap
import pickle

def explain(text):
    tfidf = pickle.load(open("model/tfidf.pkl", "rb"))
    model = pickle.load(open("model/fake_job_model.pkl", "rb"))

    X = tfidf.transform([text])

    explainer = shap.LinearExplainer(model, tfidf.transformer_list[0][1])
    shap_values = explainer(X)

    shap.plots.bar(shap_values)
