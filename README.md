# customer_churn_prediction.py
1.Data Import and Preprocessing: The script starts by downloading and extracting the dataset from Kaggle, then it loads the necessary libraries and the dataset. It also provides an introduction to the problem of customer churn prediction.

2.Descriptive Statistics: The script provides descriptive statistics for the training, testing, and original datasets, including information on data types, counts, unique values, and missing values.

3.Feature Engineering: Several feature engineering steps are defined using custom transformers and functions to preprocess the data and generate new features.

4.Model Cross Validation: The script defines a function for cross-validation of different models, including Logistic Regression, TensorFlow, XGBoost, LightGBM, and CatBoost. It evaluates the performance of each model using ROC AUC score and provides visualizations for feature importance.

5.Model Training and Evaluation: The script trains each model using cross-validation and evaluates its performance. It also optimizes hyperparameters for XGBoost and LightGBM using Optuna.

6.Voting Ensemble: The script creates a voting ensemble of the trained models with weights determined by Ridge Classifier coefficients. It evaluates the ensemble's performance and generates predictions.

7.Submission: Finally, the script generates a submission file with the predicted churn probabilities for the test dataset.
