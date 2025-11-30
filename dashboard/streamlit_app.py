"""
Streamlit dashboard for ML Service
"""
import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

API_BASE_URL = "http://localhost:8000" 

st.set_page_config(
    page_title="ML Service Dashboard",
    page_icon="🧠",
    layout="wide"
)

def call_api(endpoint, method="GET", data=None):
    """Helper function to call REST API"""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

def main():
    st.title("ML Service Dashboard")
    st.sidebar.title("Navigation")
    
    # Navigation
    page = st.sidebar.radio(
        "Go to",
        ["Status", "Datasets", "Training", "Models", "Inference", "ClearML"]
    )
    
    if page == "Status":
        show_status()
    elif page == "Datasets":
        show_datasets()
    elif page == "Training":
        show_training()
    elif page == "Models":
        show_models()
    elif page == "Inference":
        show_inference()
    elif page == "ClearML":
        show_clearml()

def show_status():
    st.header("Service Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Check Health"):
            result = call_api("/health")
            if result:
                st.success(f"✅ Status: {result['status']}")
    
    with col2:
        if st.button("Get Model Classes"):
            result = call_api("/models/classes")
            if result:
                st.write("Available models:", result["classes"])
    
    with col3:
        if st.button("Refresh All"):
            st.experimental_rerun()
    
    st.subheader("System Information")
    st.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.write(f"API Base URL: {API_BASE_URL}")

def show_datasets():
    st.header("Dataset Management")
    
    st.subheader("Upload Dataset")
    uploaded_file = st.file_uploader("Choose CSV or JSON file", type=['csv', 'json'])
    
    if uploaded_file is not None:
        if st.button("Upload"):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            response = requests.post(f"{API_BASE_URL}/datasets/upload", files=files)
            if response.status_code == 200:
                st.success("Dataset uploaded successfully!")
            else:
                st.error(f"Upload failed: {response.text}")
    
    st.subheader("Available Datasets")
    result = call_api("/datasets")
    
    if result:
        df = pd.DataFrame(result)
        if not df.empty:
            st.dataframe(df)
            
            selected_dataset = st.selectbox("Select dataset to delete", df['name'])
            if st.button("Delete Dataset", type="secondary"):
                if call_api(f"/datasets/{selected_dataset}", "DELETE"):
                    st.success("Dataset deleted!")
                    st.experimental_rerun()
        else:
            st.info("No datasets available")

def show_training():
    st.header("Model Training")
    
    datasets_result = call_api("/datasets")
    classes_result = call_api("/models/classes")
    
    if not datasets_result or not classes_result:
        st.error("Failed to load required data")
        return
    
    datasets = [d['name'] for d in datasets_result]
    model_classes = classes_result['classes']
    
    with st.form("training_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            dataset = st.selectbox("Dataset", datasets)
            model_class = st.selectbox("Model Class", model_classes)
            model_name = st.text_input("Model Name (optional)")
            experiment_name = st.text_input("Experiment Name (optional)")
        
        with col2:
            st.subheader("Hyperparameters")
            hyperparams = {}
            
            if model_class == "logreg":
                hyperparams['C'] = st.number_input("C", value=1.0)
                hyperparams['max_iter'] = st.number_input("Max Iterations", value=1000)
            elif model_class == "random_forest":
                hyperparams['n_estimators'] = st.number_input("Number of Estimators", value=100)
                hyperparams['max_depth'] = st.number_input("Max Depth", value=5)
            elif model_class == "svm":
                hyperparams['C'] = st.number_input("C", value=1.0)
                hyperparams['kernel'] = st.selectbox("Kernel", ['rbf', 'linear', 'poly'])
            elif model_class == "xgboost":
                hyperparams['n_estimators'] = st.number_input("Number of Estimators", value=100)
                hyperparams['max_depth'] = st.number_input("Max Depth", value=3)
        
        if st.form_submit_button("Start Training"):
            training_data = {
                "dataset": dataset,
                "model_class": model_class,
                "hyperparams": hyperparams,
                "model_name": model_name,
                "experiment_name": experiment_name
            }
            
            result = call_api("/train", "POST", training_data)
            if result:
                st.success("Training started successfully!")
                st.json(result)

def show_models():
    st.header("Model Management")
    
    result = call_api("/models")
    
    if result:
        if result:
            df = pd.DataFrame(result)
            st.dataframe(df)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                model_id = st.selectbox("Select Model", df['id'])
                if st.button("Get Details"):
                    model_details = call_api(f"/models/{model_id}")
                    if model_details:
                        st.json(model_details)
            
            with col2:
                if st.button("Retrain Model"):
                    if call_api(f"/models/{model_id}/retrain", "POST"):
                        st.success("Retraining started!")
            
            with col3:
                if st.button("Delete Model", type="secondary"):
                    if call_api(f"/models/{model_id}", "DELETE"):
                        st.success("Model deleted!")
                        st.experimental_rerun()
        else:
            st.info("No models available")

def show_inference():
    st.header("Model Inference")
    
    models_result = call_api("/models")
    if not models_result:
        st.error("Failed to load models")
        return
    
    ready_models = [m for m in models_result if m['status'] == 'ready']
    
    if not ready_models:
        st.warning("No trained models available for inference")
        return
    
    model_options = {f"{m['name']} ({m['model_class']})": m['id'] for m in ready_models}
    selected_model_name = st.selectbox("Select Model", list(model_options.keys()))
    model_id = model_options[selected_model_name]
    
    st.subheader("Input Features")
    
    feature_count = st.number_input("Number of features", min_value=1, max_value=100, value=4)
    
    features = []
    cols = st.columns(min(feature_count, 5))
    
    for i in range(feature_count):
        with cols[i % 5]:
            feature_value = st.number_input(f"Feature {i+1}", value=0.0, key=f"feature_{i}")
            features.append(feature_value)
    
    if st.button("Get Prediction"):
        prediction_data = {
            "model_id": model_id,
            "features": [features]  
        }
        
        result = call_api("/predict", "POST", prediction_data)
        if result:
            st.success(f"Prediction: {result['predictions'][0]}")
            
            fig = go.Figure(data=[go.Bar(x=['Prediction'], y=result['predictions'])])
            st.plotly_chart(fig)

def show_clearml():
    st.header("ClearML Experiments")
    
    if st.button("Load ClearML Experiments"):
        result = call_api("/clearml/experiments")
        
        if result and 'experiments' in result:
            experiments = result['experiments']
            if experiments:
                df = pd.DataFrame(experiments)
                st.dataframe(df)
                
                if not df.empty:
                    status_counts = df['status'].value_counts()
                    fig = px.pie(values=status_counts.values, names=status_counts.index, title="Experiment Status Distribution")
                    st.plotly_chart(fig)
            else:
                st.info("No ClearML experiments found")
        else:
            st.error("Failed to load ClearML experiments")

if __name__ == "__main__":
    main()