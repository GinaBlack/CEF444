import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.svm import SVR
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import warnings

warnings.filterwarnings("ignore") # Suppress warnings

# --- 1. Load the Data ---
try:
    # Assuming 'cleaned_dataset.csv' is in the same directory as the script
    df = pd.read_csv('cleaned_dataset.csv')
    print("Dataset loaded successfully.")
except FileNotFoundError:
    print("Error: 'cleaned_dataset.csv' not found. Please ensure the file is in the same directory.")
    exit()

# --- 2. Data Preprocessing and Feature Engineering ---

# Convert 'date' column to datetime and set as index
df['date'] = pd.to_datetime(df['date'])
df.set_index('date', inplace=True)
df.sort_index(inplace=True) # Ensure chronological order

# Select relevant columns for forecasting.
data = df[['irradiance', 'temperature', 'humidity', 'wind_speed']]

# Handle missing values (if any)
if data.isnull().sum().sum() > 0:
    print(f"Warning: Missing values found. Imputing with forward/backward fill.")
    data = data.ffill().bfill()

# --- TEMPORARY: Reduce Data Size for Faster Testing ---

print(f"Original dataset size: {len(df)} samples")

data = data.tail(10000) # Using last 10,000 data points for quicker iteration
print(f"Reduced dataset size for testing: {len(data)} samples")


# --- Feature Engineering: Create Lagged Features ---
n_lags = 24 # Number of past time steps to use as features

X = [] # Features
y = [] # Target

for i in range(n_lags, len(data)):
    X.append(data['irradiance'].iloc[i-n_lags:i].values)
    y.append(data['irradiance'].iloc[i])

X = np.array(X)
y = np.array(y)

print(f"Shape of features (X): {X.shape}")
print(f"Shape of target (y): {y.shape}")

# --- 3. Split Data into Training and Testing Sets ---
train_size = int(len(X) * 0.8)
X_train, X_test = X[0:train_size], X[train_size:]
y_train, y_test = y[0:train_size], y[train_size:]

print(f"\nTraining data points (X_train, y_train): {len(X_train)}")
print(f"Test data points (X_test, y_test): {len(X_test)}")

# --- 4. Scale Features ---
scaler_X = MinMaxScaler()
scaler_y = MinMaxScaler()

X_train_scaled = scaler_X.fit_transform(X_train)
X_test_scaled = scaler_X.transform(X_test)

y_train_reshaped = y_train.reshape(-1, 1)
y_test_reshaped = y_test.reshape(-1, 1)

y_train_scaled = scaler_y.fit_transform(y_train_reshaped).flatten()
y_test_scaled = scaler_y.transform(y_test_reshaped).flatten()


# --- 5. Implement and Fit the SVR Model ---
print("\nFitting SVR model...")

svr_model = SVR(kernel='rbf', C=10, epsilon=0.1, gamma='scale') 
svr_model.fit(X_train_scaled, y_train_scaled)
print("SVR model fitted successfully.")

# --- 6. Make Predictions ---
predictions_scaled = svr_model.predict(X_test_scaled)
predictions = scaler_y.inverse_transform(predictions_scaled.reshape(-1, 1)).flatten()

test_index_start = n_lags + (len(df) - len(data)) + train_size # Adjusted for subsetting
test_index = df.index[test_index_start : test_index_start + len(y_test)]


# --- 7. Evaluate the Model ---
rmse = np.sqrt(mean_squared_error(y_test, predictions))
mae = mean_absolute_error(y_test, predictions)

mape = np.mean(np.abs((y_test - predictions) / (y_test + 1e-8))) * 100

print(f"\nModel Performance Metrics:")
print(f"Root Mean Squared Error (RMSE): {rmse:.3f}")
print(f"Mean Absolute Error (MAE): {mae:.3f}")
print(f"Mean Absolute Percentage Error (MAPE): {mape:.3f}%")

# --- 8. Complete Visualization ---
plt.figure(figsize=(15, 8))

# Plot actual training data
actual_train_index_start = n_lags + (len(df) - len(data))
actual_train_index = df.index[actual_train_index_start : actual_train_index_start + train_size]
plt.plot(actual_train_index, y_train, label='Training Data (Actual)', color='blue', alpha=0.7)

# Plot actual test data
plt.plot(test_index, y_test, label='Test Data (Actual)', color='green', linewidth=2)

# Plot SVR predictions
plt.plot(test_index, predictions, label='SVR Predictions', color='red', linewidth=2, linestyle='--')

plt.title('Solar Irradiance Forecasting using SVR', fontsize=16, fontweight='bold')
plt.xlabel('Date', fontsize=12)
plt.ylabel('Solar Irradiance', fontsize=12)
plt.legend(fontsize=12)
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Actual vs Predicted Scatter Plot ---
plt.figure(figsize=(8, 6))
plt.scatter(y_test, predictions, color='purple', alpha=0.6)
plt.plot([min(y_test), max(y_test)], [min(y_test), max(y_test)], color='black', linestyle='--', linewidth=2)
plt.title('Actual vs Predicted Values', fontsize=14, fontweight='bold')
plt.xlabel('Actual Solar Irradiance', fontsize=12)
plt.ylabel('Predicted Solar Irradiance', fontsize=12)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# Residual Distribution Plot 
residuals = y_test - predictions
plt.figure(figsize=(8, 6))
sns.histplot(residuals, bins=50, kde=True, color='teal')
plt.title('Residual Distribution (Actual - Predicted)', fontsize=14, fontweight='bold')
plt.xlabel('Residuals', fontsize=12)
plt.ylabel('Frequency', fontsize=12)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

#  Bar Chart of Error Metrics ---
metrics = ['RMSE', 'MAE', 'MAPE']
values = [rmse, mae, mape]

plt.figure(figsize=(8, 6))
bars = plt.bar(metrics, values, color=['steelblue', 'orange', 'green'])
plt.title('Error Metrics Comparison', fontsize=14, fontweight='bold')
plt.ylabel('Value', fontsize=12)
plt.grid(True, axis='y', alpha=0.3)
plt.tight_layout()

# Annotate bars with values
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width() / 2, height, f'{height:.2f}', ha='center', va='bottom', fontsize=10)

plt.show()

# -------- other Visualisations By GinaBlack --------------------

# Constants
N_LAGS = 24  # Number of lagged time steps for features
TEST_SIZE = 0.2  # Proportion for test set
EPOCHS = 30  # Maximum training epochs for LSTM
BATCH_SIZE = 32  # Batch size for LSTM training
VALIDATION_SPLIT = 0.1  # Validation split during training

# # 5.1 Actual vs Predicted Plots

def plot_predictions_comparison(y_test, predictions, test_index):
    """Compare actual vs predicted values"""
    plt.figure(figsize=(15, 7))
    
    # Plot actual values
    plt.plot(test_index, y_test, label='Actual', color='green', linewidth=1.5)
    
    # Plot predictions
    plt.plot(test_index, predictions, color='red', label=f'SVR (RMSE: {rmse:.3f})', 
             linestyle='--', alpha=0.8)
    
    plt.title('Solar Irradiance: Actual vs Predicted')
    plt.xlabel('Date')
    plt.ylabel('Irradiance (W/m²)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

# Create test index for plotting
test_index = df.index[N_LAGS + len(X_train):N_LAGS + len(X_train) + len(y_test)]
plot_predictions_comparison(y_test, predictions, test_index)


# 5.2 Residuals Over Time

def plot_residuals(y_test, predictions, test_index, model_name='Model'):
    """Plot model residuals over time"""
    residuals = y_test - predictions
    
    plt.figure(figsize=(14, 6))
    plt.scatter(test_index, residuals, alpha=0.5, s=10, label='Daily Residuals')
    plt.axhline(0, color='red', linestyle='--', alpha=0.7)
    
    # Rolling mean of residuals
    residual_series = pd.Series(residuals, index=test_index)
    rolling_mean = residual_series.rolling(30).mean()
    plt.plot(rolling_mean.index, rolling_mean, 
             color='blue', label='30-day Moving Avg')
    
    plt.title(f'Residuals Over Time ({model_name})')
    plt.xlabel('Date')
    plt.ylabel('Prediction Error (Actual - Predicted)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

plot_residuals(y_test, predictions, test_index, 'SVR')

# 5.4 Town-wise Performance 

def analyze_town_performance(y_test, predictions, test_index, df):
    """Analyze model performance by town if data available"""
    if 'town' not in df.columns:
        print("No town information available for performance analysis")
        return None
    
    # Create results DataFrame
    results = pd.DataFrame({
        'actual': y_test,
        'predicted': predictions,
        'date': test_index
    }).set_index('date')
    
    # Join with original town data
    results = results.join(df[['town']], how='left')
    
    # Calculate metrics by town
    metrics_by_town = results.groupby('town').apply(
        lambda x: pd.Series({
            'RMSE': np.sqrt(mean_squared_error(x['actual'], x['predicted'])),
            'MAE': mean_absolute_error(x['actual'], x['predicted']),
            'MAPE': np.mean(np.abs((x['actual'] - x['predicted']) / x['actual'])) * 100
        })
    ).reset_index()
    
    # Visualization
    plt.figure(figsize=(12, 6))
    metrics_by_town.melt(id_vars='town', var_name='metric').pipe(
        (sns.barplot, 'data'), x='town', y='value', hue='metric')
    plt.title('Model Performance Metrics by Town')
    plt.ylabel('Error Value')
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.show()
    
    return metrics_by_town

# Analyze for both models
print("\nSVR Town Performance:")
svr_town_metrics = analyze_town_performance(y_test, predictions, test_index, df)

