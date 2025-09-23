import joblib
import shap
import pandas as pd
import numpy as np
import json
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from src.services.llm_utils import llm
from src.core.config import config
from src.db.database import get_db_connection
from datetime import datetime

model = joblib.load(config.MODEL_PATH)
preprocessor = joblib.load(config.PREPROCESSOR_PATH)
explainer = shap.TreeExplainer(model)

explain_prompt = PromptTemplate(
    template="""
Generate a concise explanation for the churn prediction in {language}.
Prediction (0=no churn, 1=churn): {pred}
Churn Probability: {prob:.2f}
Key SHAP values: {shap}
Customer data: {data}

List only the top 3 factors affecting the prediction as bullet points.
Respond in {language} with no additional details.
    """,
    input_variables=["pred", "prob", "shap", "data", "language"]
)
explain_chain = LLMChain(llm=llm, prompt=explain_prompt)

def predict_and_explain(features: dict, query: str, customer_id: str = None, language: str = 'en') -> str:
    try:
        if customer_id:
            conn = get_db_connection()
            try:
                customer_df = pd.read_sql("SELECT * FROM customers WHERE CustomerId = ?", conn, params=(customer_id,))
                if not customer_df.empty:
                    customer_data = customer_df.iloc[0].to_dict()
                    pred = int(customer_data["Exited"])
                    prob = 1.0 if pred == 1 else 0.0

                    explanation = explain_chain.invoke({
                        "pred": pred,
                        "prob": prob,
                        "shap": "Ground truth from dataset",
                        "data": customer_data,
                        "language": language
                    })['text']

                    return (
                        f"Customer Information:\n{json.dumps(customer_data, indent=2)}\n\n"
                        f"{explanation}\n\n"
                        f"Actual Churn: {pred} (1 = Churned, 0 = Retained)"
                    )
            finally:
                conn.close()

        # Model prediction for new customer
        df = pd.DataFrame([features])
        processed = preprocessor.transform(df)
        pred = int(model.predict(processed)[0])  # Ensure scalar
        prob = float(model.predict_proba(processed)[0][1])  # Ensure scalar for positive class

        # Handle SHAP values
        shap_values = explainer.shap_values(processed)
        # For binary classification, select the positive class SHAP values
        shap_vals = shap_values[1] if isinstance(shap_values, list) and len(shap_values) > 1 else shap_values
        # Flatten if necessary
        shap_vals = np.array(shap_vals).flatten()
        shap_dict = dict(zip(preprocessor.get_feature_names_out(), shap_vals.tolist()))
        top_factors = dict(sorted(shap_dict.items(), key=lambda x: abs(x[1]), reverse=True)[:3])

        explanation = explain_chain.invoke({
            "pred": pred,
            "prob": prob,
            "shap": top_factors,
            "data": features,
            "language": language
        })['text']

        # Save prediction to database
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO predictions (customer_id, features, prediction, probability, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    customer_id if customer_id else 'unknown',
                    json.dumps(features),
                    pred,
                    prob,
                    datetime.now().isoformat()
                )
            )
            conn.commit()
        finally:
            conn.close()

        return (
            f"Customer Information:\n{json.dumps(features, indent=2)}\n\n"
            f"{explanation}\n\n"
            f"Predicted Churn: {pred}, Probability: {prob:.2f}"
        )
    except Exception as e:
        return f"Error: {str(e)}" if language == 'en' else f"خطأ: {str(e)}"