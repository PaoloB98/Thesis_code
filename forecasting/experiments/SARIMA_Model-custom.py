import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import timedelta
from pandas.plotting import register_matplotlib_converters
from statsmodels.tsa.stattools import acf, pacf
from statsmodels.tsa.statespace.sarimax import SARIMAX
register_matplotlib_converters()
from time import time
from numpy.linalg import LinAlgError

#read data
def parser(s):
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')

weekly_conn = pd.read_csv('../weekDist.csv', usecols = ['time', 'num_usr'], parse_dates=[0], index_col=0, date_parser=parser)

weekly_conn = weekly_conn.squeeze().astype(int)

#infer the frequency of the data
weekly_conn = weekly_conn.asfreq(pd.infer_freq(weekly_conn.index))

start_date = datetime(2022, 6, 10, 0, 0, 0)
end_date = datetime(2022, 6, 13, 0, 0, 0)

train_weekly_conn = weekly_conn[start_date:end_date]

plt.figure(figsize=(10,4))
plt.plot(train_weekly_conn)
plt.title('Number of connected devices per hour', fontsize=20)
plt.ylabel('Number of connected devices', fontsize=16)

first_diff = train_weekly_conn.diff()[1:]
first_diff.shape

plt.figure(figsize=(10,4))
plt.plot(first_diff)
plt.title('Connecter Devices per Hour', fontsize=20)
plt.ylabel('Conn Dev', fontsize=16)


acf_vals = acf(first_diff)

num_lags = 19
plt.figure(figsize=(10,4))
plt.bar(range(num_lags), acf_vals[:num_lags])

pacf_vals = pacf(first_diff)
num_lags = 15
plt.figure(figsize=(10,4))
plt.bar(range(num_lags), pacf_vals[:num_lags])

train_end = datetime(2022, 6, 14, 0, 0, 0)
test_end = datetime(2022, 6, 16, 23, 0, 0)

train_data = weekly_conn[:train_end]
test_data = weekly_conn[train_end + timedelta(hours=1):test_end]

my_order = (1,1,1)
my_seasonal_order = (1, 1, 1, 24)
# define model
model = SARIMAX(train_data, order=my_order, seasonal_order=my_seasonal_order)

#fit the model
start = time()
try:
    model_fit = model.fit()
except LinAlgError:
    print("\n\n Cannot fit the model!!!\n\n")

end = time()
print('Model Fitting Time:', end - start)

#summary of the model
print(model_fit.summary())

#get the predictions and residuals
predictions = model_fit.forecast(len(test_data))
predictions = pd.Series(predictions, index=test_data.index)
predictions = predictions.squeeze()
residuals = test_data - predictions

a = plt.figure(figsize=(10,4))
plt.plot(residuals)
plt.axhline(0, linestyle='--', color='k')
plt.title('Residuals from SARIMA Model', fontsize=20)
plt.ylabel('Error', fontsize=16)

plt.figure(figsize=(10,4))

plt.plot(weekly_conn)
plt.plot(predictions)

plt.legend(('Data', 'Predictions'), fontsize=16)

plt.title('tst', fontsize=20)
plt.ylabel('sss', fontsize=16)
for year in range(start_date.year,end_date.year):
    plt.axvline(pd.to_datetime(str(year)+'-01-01'), color='k', linestyle='--', alpha=0.2)
    
mean_per_err = round(np.mean(abs(residuals/test_data)),4)
mean_sqr_err = np.sqrt(np.mean(residuals**2))
print('Mean Absolute Percent Error:', mean_per_err)
print('Root Mean Squared Error:', mean_sqr_err)

