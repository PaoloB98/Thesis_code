import pandas as pd
import numpy as np
from datetime import datetime
from datetime import timedelta
from pandas.plotting import register_matplotlib_converters
from statsmodels.tsa.statespace.sarimax import SARIMAX
register_matplotlib_converters()
from time import time
from numpy.linalg import LinAlgError
from itertools import product

#read data
def parser(s):
    return datetime.strptime(s, '%Y-%m-%d %H:%M:%S')

weekly_conn = pd.read_csv('../weekDist.csv', usecols = ['time', 'num_usr'], parse_dates=[0], index_col=0, date_parser=parser)

weekly_conn = weekly_conn.squeeze().astype(int)

#infer the frequency of the data
weekly_conn = weekly_conn.asfreq(pd.infer_freq(weekly_conn.index))

train_end = datetime(2022, 6, 14, 0, 0, 0)
test_end = datetime(2022, 6, 16, 23, 0, 0)

train_data = weekly_conn[:train_end]
test_data = weekly_conn[train_end + timedelta(hours=1):test_end]

# Open a file with access mode 'a'
file_object = open('results.txt', 'w')

first_iter = True

for i,x,y,z,k,l in product([0, 1, 2], repeat=6):
    my_order = (i,x,y)
    my_seasonal_order = (z, k, l, 24)
    print('STARTING ITERATION ON ' + str(my_order) + ' ' + str(my_seasonal_order) + '\n')
    # define model
    model = SARIMAX(train_data, order=my_order, seasonal_order=my_seasonal_order)
    
        #fit the model
    start = time()
    
    
    try:
        model_fit = model.fit()
    except LinAlgError:
        print("\n\n Cannot fit the model!!!\n\n")
        continue
    
    end = time()
    print('Model Fitting Time:', end - start)
    
    #summary of the model
    print(model_fit.summary())
    
    #get the predictions and residuals
    predictions = model_fit.forecast(len(test_data))
    predictions = pd.Series(predictions, index=test_data.index)
    predictions = predictions.squeeze()
    residuals = test_data - predictions
    
        
    mean_per_err = round(np.mean(abs(residuals/test_data)),4)
    mean_sqr_err = np.sqrt(np.mean(residuals**2))
    print('Mean Absolute Percent Error:', mean_per_err)
    print('Root Mean Squared Error:', mean_sqr_err)
    
    
    # Append 'hello' at the end of file
    to_print = 'Result for ' + str(my_order) + ' ' + str(my_seasonal_order) + '\n'
    to_print = to_print + 'Mean Absolute Percent Error:' + str(mean_per_err) + '\n'
    to_print = to_print + 'Root Mean Squared Error:' + str(mean_sqr_err) + '\n'
    to_print = to_print + '----------------------------------\n' 
    file_object.write(to_print)
    
    if first_iter :
        first_iter = False
        min_per_err = mean_per_err
        min_sqr_err = mean_sqr_err
        min_per_order=my_order
        min_per_order_S=my_seasonal_order
        min_sqr_order=my_order
        min_sqr_order_S=my_seasonal_order
    
    if(min_per_err>mean_per_err):
        min_per_order=my_order
        min_per_order_S=my_seasonal_order
    if(min_sqr_err>mean_sqr_err):
        min_sqr_order=my_order
        min_sqr_order_S=my_seasonal_order
    
# Close the file
# Append 'hello' at the end of file
to_print = 'Minimum MEAN SQUARE ERROR has been obtained with ' + str(min_sqr_order) + ' ' + str(min_sqr_order_S) + '\n'
to_print = to_print + '----------------------------------\n' 
to_print = to_print + 'Minimum ABSOLUTE PERCENT ERROR has been obtained with ' + str(min_per_order) + ' ' + str(min_per_order_S) + '\n'
to_print = to_print + '----------------------------------\n' 
file_object.write(to_print)

file_object.close()