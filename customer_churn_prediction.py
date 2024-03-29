import os
import sys
from tempfile import NamedTemporaryFile
from urllib.request import urlopen
from urllib.parse import unquote, urlparse
from urllib.error import HTTPError
from zipfile import ZipFile
import tarfile
import shutil

CHUNK_SIZE = 40960
DATA_SOURCE_MAPPING = 'bank-customer-churn-prediction:https%3A%2F%2Fstorage.googleapis.com%2Fkaggle-data-sets%2F2008274%2F3322096%2Fbundle%2Farchive.zip%3FX-Goog-Algorithm%3DGOOG4-RSA-SHA256%26X-Goog-Credential%3Dgcp-kaggle-com%2540kaggle-161607.iam.gserviceaccount.com%252F20240212%252Fauto%252Fstorage%252Fgoog4_request%26X-Goog-Date%3D20240212T042656Z%26X-Goog-Expires%3D259200%26X-Goog-SignedHeaders%3Dhost%26X-Goog-Signature%3D41fb29683b646dec72686f9d645aef504eee1d3d7a10e613a7c1e1e97d539f1608069eec5d3195eaa390d133048a3583cd22f7b5e9d753ab3cb460cfdc009a305d919714c8a08b98c26e84a7d8b012fb9eb88879042d2ae8bd64d26f8ccb31165fce95175c5c3a8d91d76078ebb290656ac845da05d64a93b21e809a514b97ba26337fc96999f2a0249d2a6a5eb623bfbb5a250e5ead07cd4fd28a3ff9071fd79e0cd36a471b7a5ec83b0cf824dd05a45e81ae995f589cb4af8cacd1950de14917dd716c73d84bd64ba0d287e3fde97d933466dc83837ff7cd4c6cf729798b2734abb30b47b65a29a26df48eb2b6c8652d4cdf6298dc74f139e6f10e6cab5530'

KAGGLE_INPUT_PATH='/kaggle/input'
KAGGLE_WORKING_PATH='/kaggle/working'
KAGGLE_SYMLINK='kaggle'

!umount /kaggle/input/ 2> /dev/null
shutil.rmtree('/kaggle/input', ignore_errors=True)
os.makedirs(KAGGLE_INPUT_PATH, 0o777, exist_ok=True)
os.makedirs(KAGGLE_WORKING_PATH, 0o777, exist_ok=True)

try:
  os.symlink(KAGGLE_INPUT_PATH, os.path.join("..", 'input'), target_is_directory=True)
except FileExistsError:
  pass
try:
  os.symlink(KAGGLE_WORKING_PATH, os.path.join("..", 'working'), target_is_directory=True)
except FileExistsError:
  pass

for data_source_mapping in DATA_SOURCE_MAPPING.split(','):
    directory, download_url_encoded = data_source_mapping.split(':')
    download_url = unquote(download_url_encoded)
    filename = urlparse(download_url).path
    destination_path = os.path.join(KAGGLE_INPUT_PATH, directory)
    try:
        with urlopen(download_url) as fileres, NamedTemporaryFile() as tfile:
            total_length = fileres.headers['content-length']
            print(f'Downloading {directory}, {total_length} bytes compressed')
            dl = 0
            data = fileres.read(CHUNK_SIZE)
            while len(data) > 0:
                dl += len(data)
                tfile.write(data)
                done = int(50 * dl / int(total_length))
                sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {dl} bytes downloaded")
                sys.stdout.flush()
                data = fileres.read(CHUNK_SIZE)
            if filename.endswith('.zip'):
              with ZipFile(tfile) as zfile:
                zfile.extractall(destination_path)
            else:
              with tarfile.open(tfile.name) as tarfile:
                tarfile.extractall(destination_path)
            print(f'\nDownloaded and uncompressed: {directory}')
    except HTTPError as e:
        print(f'Failed to load (likely expired) {download_url} to path {destination_path}')
        continue
    except OSError as e:
        print(f'Failed to load {download_url} to path {destination_path}')
        continue

print('Data source import complete.')



import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
import optuna

from category_encoders import OneHotEncoder, MEstimateEncoder, CatBoostEncoder, OrdinalEncoder
from sklearn import set_config
from sklearn.inspection import permutation_importance
from sklearn.model_selection import StratifiedKFold, RepeatedStratifiedKFold
from sklearn.feature_selection import SequentialFeatureSelector
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.metrics import roc_auc_score, roc_curve, make_scorer, f1_score
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import SimpleImputer, IterativeImputer, KNNImputer
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.base import BaseEstimator, TransformerMixin, ClassifierMixin, clone
from sklearn.preprocessing import FunctionTransformer, StandardScaler, LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression, RidgeClassifier, RidgeClassifierCV
from sklearn.naive_bayes import GaussianNB, BernoulliNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.ensemble import VotingClassifier, StackingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.gaussian_process import GaussianProcessClassifier
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform
from xgboost import XGBClassifier, XGBRFClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier

sns.set_theme(style = 'white', palette = 'viridis')
pal = sns.color_palette('viridis')

pd.set_option('display.max_rows', 100)
set_config(transform_output = 'pandas')
pd.options.mode.chained_assignment = None

train = pd.read_csv(r'/kaggle/input/playground-series-s4e1/train.csv', index_col = 'id').astype({'IsActiveMember' : np.uint8, 'HasCrCard' : np.uint8})
test = pd.read_csv(r'/kaggle/input/playground-series-s4e1/test.csv', index_col = 'id').astype({'IsActiveMember' : np.uint8, 'HasCrCard' : np.uint8})
orig_train = pd.read_csv(r'/kaggle/input/bank-customer-churn-prediction/Churn_Modelling.csv', index_col = 'RowNumber')

"""#Training Data"""
train.head(10)

desc = pd.DataFrame(index = list(train))
desc['type'] = train.dtypes
desc['count'] = train.count()
desc['nunique'] = train.nunique()
desc['%unique'] = desc['nunique'] / len(train) * 100
desc['null'] = train.isnull().sum()
desc['%null'] = desc['null'] / len(train) * 100
desc['min'] = train.min()
desc['max'] = train.max()
desc

"""#Test Data Set"""
test.head(10)

desc = pd.DataFrame(index = list(test))
desc['type'] = test.dtypes
desc['count'] = test.count()
desc['nunique'] = test.nunique()
desc['%unique'] = desc['nunique'] / len(test) * 100
desc['null'] = test.isnull().sum()
desc['%null'] = desc['null'] / len(test) * 100
desc['min'] = test.min()
desc['max'] = test.max()
desc

"""#Original Data set"""
orig_train.head(10)

desc = pd.DataFrame(index = list(orig_train))
desc['type'] = orig_train.dtypes
desc['count'] = orig_train.count()
desc['nunique'] = orig_train.nunique()
desc['%unique'] = desc['nunique'] / len(orig_train) * 100
desc['null'] = orig_train.isnull().sum()
desc['%null'] = desc['null'] / len(orig_train) * 100
desc['min'] = orig_train.min()
desc['max'] = orig_train.max()
desc

numerical_features = list(test._get_numeric_data())
categorical_features = list(test.drop(numerical_features, axis = 1))

"""#Building ML model"""
X = pd.concat([orig_train, train]).reset_index(drop = True)
y = X.pop('Exited')

orig_comp_combo = train.merge(orig_train, on = list(test), how = 'left')
orig_comp_combo.index = train.index

orig_test_combo = test.merge(orig_train, on = list(test), how = 'left')
orig_test_combo.index = test.index

seed = 42
splits = 30
skf = StratifiedKFold(n_splits = splits, random_state = seed, shuffle = True)
tf.keras.utils.set_random_seed(seed)
tf.config.experimental.enable_op_determinism()

"""# Feature Engineering"""

def nullify(x):
    x_copy = x.copy()
    x_copy['Balance'] = x_copy['Balance'].replace({0 : np.nan})
    return x_copy

Nullify = FunctionTransformer(nullify)

def salary_rounder(x):
    x_copy = x.copy()
    x_copy['EstimatedSalary'] = (x_copy['EstimatedSalary'] * 100).astype(np.uint64)
    return x_copy

SalaryRounder = FunctionTransformer(salary_rounder)

def age_rounder(x):
    x_copy = x.copy()
    x_copy['Age'] = (x_copy['Age'] * 10).astype(np.uint16)
    return x_copy

AgeRounder = FunctionTransformer(age_rounder)

def balance_rounder(x):
    x_copy = x.copy()
    x_copy['Balance'] = (x_copy['Balance'] * 100).astype(np.uint64)
    return x_copy

BalanceRounder = FunctionTransformer(balance_rounder)

def feature_generator(x):

    x_copy = x.copy()
    #x_copy['IsSenior'] = (x_copy['Age'] >= 600).astype(np.uint8)
    x_copy['IsActive_by_CreditCard'] = x_copy['HasCrCard'] * x_copy['IsActiveMember']
    x_copy['Products_Per_Tenure'] =  x_copy['Tenure'] / x_copy['NumOfProducts']
    x_copy['ZeroBalance'] = (x_copy['Balance'] == 0).astype(np.uint8)
    x_copy['AgeCat'] = np.round(x_copy.Age/20).astype(np.uint16)#.astype('category')
    x_copy['AllCat'] = x_copy['Surname']+x_copy['Geography']+x_copy['Gender']+x_copy.EstimatedSalary.astype('str')+x_copy.CreditScore.astype('str')+x_copy.Age.astype('str')+x_copy.NumOfProducts.astype('str')+x_copy.Tenure.astype('str')+x_copy.CustomerId.astype('str')#+np.round(x_copy.IsActiveMember).astype('str')

    return x_copy

FeatureGenerator = FunctionTransformer(feature_generator)

def svd_rounder(x):

    x_copy = x.copy()
    for col in [column for column in list(x) if 'SVD' in column]:
        x_copy[col] = (x_copy[col] * 1e18).astype(np.int64)

    return x_copy

SVDRounder = FunctionTransformer(svd_rounder)

class FeatureDropper(BaseEstimator, TransformerMixin):

    def __init__(self, cols):
        self.cols = cols

    def fit(self, x, y):
        return self

    def transform(self, x):
        return x.drop(self.cols, axis = 1)

class Categorizer(BaseEstimator, TransformerMixin):

    def __init__(self, cols : list):
        self.cols = cols

    def fit(self, x, y):
        return self

    def transform(self, x):
        return x.astype({cat : 'category' for cat in self.cols})

class Vectorizer(BaseEstimator, TransformerMixin):

    def __init__(self, max_features = 1000, cols = ['Surname'], n_components = 3):
        self.max_features = max_features
        self.cols = cols
        self.n_components = n_components

    def fit(self, x, y):
        self.vectorizer_dict = {}
        self.decomposer_dict = {}

        for col in self.cols:
            self.vectorizer_dict[col] = TfidfVectorizer(max_features = self.max_features).fit(x[col].astype(str), y)
            self.decomposer_dict[col] = TruncatedSVD(random_state = seed, n_components = self.n_components).fit(
                self.vectorizer_dict[col].transform(x[col].astype(str)), y
            )

        return self

    def transform(self, x):
        vectorized = {}

        for col in self.cols:
            vectorized[col] = self.vectorizer_dict[col].transform(x[col].astype(str))
            vectorized[col] = self.decomposer_dict[col].transform(vectorized[col])

        vectorized_df = pd.concat([pd.DataFrame(vectorized[col]).rename({
            f'truncatedsvd{i}' : f'{col}SVD{i}' for i in range(self.n_components)
        }, axis = 1) for col in self.cols], axis = 1)

        return pd.concat([x.reset_index(drop = True), vectorized_df], axis = 1)

"""# Model Cross Validation
Performance Analysis
"""

def cross_val_score(estimator, cv = skf, label = '', include_original = True, show_importance = False, add_reverse = False):

    X = train.copy()
    y = X.pop('Exited')

    #initiate prediction arrays and score lists
    val_predictions = np.zeros((len(X)))
    train_scores, val_scores= [], []

    feature_importances_table = pd.DataFrame({'value' : 0}, index = list(X.columns))

    test_predictions = np.zeros((len(test)))

    #training model, predicting prognosis probability, and evaluating metrics
    for fold, (train_idx, val_idx) in enumerate(cv.split(X, y)):

        model = clone(estimator)

        #define train set
        X_train = X.iloc[train_idx].reset_index(drop = True)
        y_train = y.iloc[train_idx].reset_index(drop = True)

        #define validation set
        X_val = X.iloc[val_idx].reset_index(drop = True)
        y_val = y.iloc[val_idx].reset_index(drop = True)

        if include_original:
            X_train = pd.concat([orig_train.drop('Exited', axis = 1), X_train]).reset_index(drop = True)
            y_train = pd.concat([orig_train.Exited, y_train]).reset_index(drop = True)

        if add_reverse:
            X_train = pd.concat([X_train, X_train.iloc[::-1]]).reset_index(drop = True)
            y_train = pd.concat([y_train, y_train.iloc[::-1]]).reset_index(drop = True)

        #train model
        model.fit(X_train, y_train)

        #make predictions
        train_preds = model.predict_proba(X_train)[:, 1]
        val_preds = model.predict_proba(X_val)[:, 1]

        val_predictions[val_idx] += val_preds
        test_predictions += model.predict_proba(test)[:, 1] / cv.get_n_splits()
        if show_importance:
            feature_importances_table['value'] += permutation_importance(model, X_val, y_val, random_state = seed, scoring = make_scorer(roc_auc_score, needs_proba = True), n_repeats = 5).importances_mean / cv.get_n_splits()

        #evaluate model for a fold
        train_score = roc_auc_score(y_train, train_preds)
        val_score = roc_auc_score(y_val, val_preds)

        #print(f'Fold {fold}: {val_score:.5f}')

        #append model score for a fold to list
        train_scores.append(train_score)
        val_scores.append(val_score)

    if show_importance:
        plt.figure(figsize = (20, 30))
        plt.title(f'Features with Biggest Importance of {np.mean(val_scores):.5f} ± {np.std(val_scores):.5f} Model', size = 25, weight = 'bold')
        sns.barplot(feature_importances_table.sort_values('value', ascending = False).T, orient = 'h', palette = 'viridis')
        plt.show()
    else:
        print(f'Val Score: {np.mean(val_scores):.5f} ± {np.std(val_scores):.5f} | Train Score: {np.mean(train_scores):.5f} ± {np.std(train_scores):.5f} | {label}')

    val_predictions = np.where(orig_comp_combo.Exited_y == 1, 0, np.where(orig_comp_combo.Exited_y == 0, 1, val_predictions))
    test_predictions = np.where(orig_test_combo.Exited == 1, 0, np.where(orig_test_combo.Exited == 0, 1, test_predictions))

    return val_scores, val_predictions, test_predictions

score_list, oof_list, predict_list = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

cat_features = ['CustomerId', 'Surname', 'EstimatedSalary', 'Geography', 'Gender', 'Tenure', 'Age', 'NumOfProducts', 'IsActiveMember', 'CreditScore', 'AllCat', 'IsActive_by_CreditCard']

"""# Logistic Regression"""

Log = make_pipeline(
    SalaryRounder,
    AgeRounder,
    FeatureGenerator,
    Vectorizer(cols = ['Surname', 'AllCat', 'EstimatedSalary', 'CreditScore'], max_features = 500, n_components = 4),
    CatBoostEncoder(cols = cat_features + [f'SurnameSVD{i}' for i in range(4)]),# + [f'AllCatSVD{i}' for i in range(6)] + [f'EstimatedSalarySVD{i}' for i in range(6)] + [f'CreditScoreSVD{i}' for i in range(6)]),
    StandardScaler(),
    LogisticRegression(random_state = seed, max_iter = 1000000000)
)

_, oof_list['Log'], predict_list['Log'] = cross_val_score(Log)


class TensorFlower(BaseEstimator, ClassifierMixin):

    def fit(self, x, y):
        inputs = tf.keras.Input((x.shape[1]))
        inputs_norm = tf.keras.layers.BatchNormalization()(inputs)

        z = tf.keras.layers.Dense(32)(inputs_norm)
        z = tf.keras.layers.BatchNormalization()(z)
        z = tf.keras.layers.LeakyReLU()(z)
        #z = tf.keras.layers.Dropout(.4)(z)

        z = tf.keras.layers.Dense(64)(z)
        z = tf.keras.layers.BatchNormalization()(z)
        z = tf.keras.layers.LeakyReLU()(z)
        #z = tf.keras.layers.Dropout(.4)(z)

        z = tf.keras.layers.Dense(16)(z)
        z = tf.keras.layers.BatchNormalization()(z)
        z = tf.keras.layers.LeakyReLU()(z)
        #z = tf.keras.layers.Dropout(.4)(z)

        z = tf.keras.layers.Dense(4)(z)
        z = tf.keras.layers.BatchNormalization()(z)
        z = tf.keras.layers.LeakyReLU()(z)
        #z = tf.keras.layers.Dropout(.4)(z)

        z = tf.keras.layers.Dense(1)(z)
        z = tf.keras.layers.BatchNormalization()(z)
        outputs = tf.keras.activations.sigmoid(z)

        self.model = tf.keras.Model(inputs, outputs)
        self.model.compile(loss = 'binary_crossentropy', optimizer = tf.keras.optimizers.AdamW(1e-4))

        self.model.fit(x.to_numpy(), y, epochs = 10, verbose = 0)
        self.classes_ = np.unique(y)

        return self
    def predict_proba(self, x):
        predictions = np.zeros((len(x), 2))
        predictions[:, 1] = self.model.predict(x, verbose = 0)[:, 0]
        predictions[:, 0] = 1 - predictions[:, 1]
        return predictions
    def predict(self, x):
        return np.argmax(self.predict_proba(x), axis = 1)

TensorFlowey = make_pipeline(
    SalaryRounder,
    AgeRounder,
    FeatureGenerator,
    #Vectorizer(cols = ['Surname', 'AllCat', 'EstimatedSalary', 'CreditScore'], max_features = 500, n_components = 6),
    CatBoostEncoder(cols = cat_features),
    TensorFlower()
)

_, oof_list['TF'], predict_list['TF'] = cross_val_score(TensorFlowey)

"""# XGBoost"""

def xgb_objective(trial):
    params = {
        'eta' : trial.suggest_float('eta', .001, .3, log = True),
        'max_depth' : trial.suggest_int('max_depth', 2, 30),
        'subsample' : trial.suggest_float('subsample', .5, 1),
        'colsample_bytree' : trial.suggest_float('colsample_bytree', .1, 1),
        'min_child_weight' : trial.suggest_float('min_child_weight', .1, 20, log = True),
        'reg_lambda' : trial.suggest_float('reg_lambda', .01, 20, log = True),
        'reg_alpha' : trial.suggest_float('reg_alpha', .01, 10, log = True),
        'n_estimators' : 1000,
        'random_state' : seed,
        'tree_method' : 'hist',
    }

    optuna_model = make_pipeline(
        SalaryRounder,
        AgeRounder,
        FeatureGenerator,
        Vectorizer(cols = ['Surname', 'AllCat', 'EstimatedSalary', 'CustomerId'], max_features = 1000, n_components = 3),
        CatBoostEncoder(cols = ['CustomerId', 'Surname', 'EstimatedSalary', 'AllCat', 'CreditScore']),
        MEstimateEncoder(cols = ['Geography', 'Gender']),
        XGBClassifier(**params)
    )

    optuna_score, _, _ = cross_val_score(optuna_model)

    return np.mean(optuna_score)

xgb_study = optuna.create_study(direction = 'maximize')

#xgb_study.optimize(xgb_objective, 50)

xgb_params = {'eta': 0.04007938900538817, 'max_depth': 5, 'subsample': 0.8858539721226424, 'colsample_bytree': 0.41689519430449395, 'min_child_weight': 0.4225662401139526, 'reg_lambda': 1.7610231110037127, 'reg_alpha': 1.993860687732973}

XGB = make_pipeline(
    SalaryRounder,
    AgeRounder,
    FeatureGenerator,
    Vectorizer(cols = ['Surname', 'AllCat', 'EstimatedSalary', 'CustomerId'], max_features = 1000, n_components = 3),
    CatBoostEncoder(cols = ['CustomerId', 'Surname', 'EstimatedSalary', 'AllCat', 'CreditScore']),
    MEstimateEncoder(cols = ['Geography', 'Gender']),
    XGBClassifier(**xgb_params, random_state = seed, tree_method = 'hist', n_estimators = 1000)
)

_, oof_list['XGB'], predict_list['XGB'] = cross_val_score(XGB, show_importance = False)

"""# LightGBM"""

def lgb_objective(trial):
    params = {
        'learning_rate' : trial.suggest_float('learning_rate', .001, .1, log = True),
        'max_depth' : trial.suggest_int('max_depth', 2, 20),
        'subsample' : trial.suggest_float('subsample', .5, 1),
        'min_child_weight' : trial.suggest_float('min_child_weight', .1, 15, log = True),
        'reg_lambda' : trial.suggest_float('reg_lambda', .1, 20, log = True),
        'reg_alpha' : trial.suggest_float('reg_alpha', .1, 10, log = True),
        'n_estimators' : 1000,
        'random_state' : seed,
        #'boosting_type' : 'dart',
    }

    optuna_model = make_pipeline(
        SalaryRounder,
        AgeRounder,
        FeatureGenerator,
        Vectorizer(cols = ['Surname', 'AllCat'], max_features = 1000, n_components = 3),
        CatBoostEncoder(cols = ['Surname', 'AllCat', 'CreditScore', 'Age']),
        MEstimateEncoder(cols = ['Geography', 'Gender', 'NumOfProducts']),
        StandardScaler(),
        LGBMClassifier(**params)
    )

    optuna_score, _, _ = cross_val_score(optuna_model)

    return np.mean(optuna_score)

lgb_study = optuna.create_study(direction = 'maximize')

#lgb_study.optimize(lgb_objective, 100)

lgb_params = {'learning_rate': 0.01864960338160943, 'max_depth': 9, 'subsample': 0.6876252164703066, 'min_child_weight': 0.8117588782708633, 'reg_lambda': 6.479178739677389, 'reg_alpha': 3.2952573115561234}

LGB = make_pipeline(
    SalaryRounder,
    AgeRounder,
    FeatureGenerator,
    Vectorizer(cols = ['Surname', 'AllCat'], max_features = 1000, n_components = 3),
    CatBoostEncoder(cols = ['Surname', 'AllCat', 'CreditScore', 'Age']),
    MEstimateEncoder(cols = ['Geography', 'Gender', 'NumOfProducts']),
    StandardScaler(),
    LGBMClassifier(**lgb_params, random_state = seed, n_estimators = 1000)
)

_, oof_list['LGB'], predict_list['LGB'] = cross_val_score(LGB, show_importance = False)

"""# CatBoost"""

CB = make_pipeline(
    SalaryRounder,
    AgeRounder,
    FeatureGenerator,
    Vectorizer(cols = ['Surname', 'AllCat'], max_features = 1000, n_components = 4),
    SVDRounder,
    CatBoostClassifier(random_state = seed, verbose = 0, cat_features = cat_features + [f'SurnameSVD{i}' for i in range(4)], has_time = True)
)

_, oof_list['CB'], predict_list['CB'] = cross_val_score(CB, show_importance = False)

CB_Bayes = make_pipeline(
    SalaryRounder,
    AgeRounder,
    FeatureGenerator,
    Vectorizer(cols = ['Surname', 'AllCat'], max_features = 1000, n_components = 4),
    SVDRounder,
    CatBoostClassifier(random_state = seed, verbose = 0, cat_features = cat_features + [f'SurnameSVD{i}' for i in range(4)], bootstrap_type = 'Bayesian', has_time = True)
)

_, oof_list['CB_Bayes'], predict_list['CB_Bayes'] = cross_val_score(CB_Bayes, show_importance = False)

CB_Bernoulli = make_pipeline(
    SalaryRounder,
    AgeRounder,
    FeatureGenerator,
    Vectorizer(cols = ['Surname', 'AllCat'], max_features = 1000, n_components = 4),
    SVDRounder,
    CatBoostClassifier(random_state = seed, verbose = 0, cat_features = cat_features + [f'SurnameSVD{i}' for i in range(4)], bootstrap_type = 'Bernoulli', has_time = True)
)

_, oof_list['CB_Bernoulli'], predict_list['CB_Bernoulli'] = cross_val_score(CB_Bernoulli, show_importance = False)


weights = RidgeClassifier(random_state = seed).fit(oof_list, train.Exited).coef_[0]
weights /= weights.sum()
pd.DataFrame(weights, index = list(oof_list), columns = ['weight per model'])

#_, ensemble_oof, predictions = cross_val_score(voter, show_importance = False)
print(f'Score: {(roc_auc_score(train.Exited, oof_list.to_numpy() @ weights)):.5f}')
predictions = predict_list.to_numpy() @ weights

"""# Submission of ML model"""

submission = test.copy()
submission['Exited'] = np.where(orig_test_combo.Exited == 1, 0, np.where(orig_test_combo.Exited == 0, 1, predictions))

submission.Exited.to_csv('submission.csv')

plt.figure(figsize = (15, 10), dpi = 300)
sns.kdeplot(submission.Exited, fill = True)
plt.title("Distribution of Customer Churn Probability", weight = 'bold', size = 25)
plt.show()
