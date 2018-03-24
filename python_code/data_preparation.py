import pandas as pd
import os


def load_file(path, file):
    df = pd.read_csv(path + file,
                 parse_dates={'date_time' : ['tstp']}, infer_datetime_format=True, 
                 low_memory=False, na_values=['nan','?'], index_col='date_time')
    df.columns = ['id', 'electricity']
    df['electricity'] = df['electricity'].convert_objects(convert_numeric=True)
    df = df.groupby('id').resample('h').sum()
    return df


def prepare_data(path, h_params):
    files = os.listdir(path)
    for file in files:
        df = load_file(path, file)
        



def create_x_tensors(data, n_in, dropNaN=True):
    """
    Creates X tensors for LSTM time series prediction

    Output has shape (samples, timesteps, features)
    """
    # create lagged variables
    cols = list()
    for i in range(n_in, 0, -1):
        cols.append(data.shift(i))
    lagged_df = pd.concat(cols, axis=1)
    if dropNaN:
        lagged_df.dropna(inplace=True)

    # reshape data to shape [samples, timesteps, features]
    return lagged_df.values.reshape((lagged_df.shape[0], n_in, n_features))


def create_y_tensor(data, n_out=1, dropNaN=True):
    """
    Creates Y tensor for LSTM time series prediction
    """
    dff = pd.DataFrame(data)
    cols = list()
    for i in range(0, n_out):
        cols.append(dff.shift(-i))
    lagged_df = pd.concat(cols, axis=1)
    if dropNaN:
        lagged_df.dropna(inplace=True)

    # reshape data to shape [samples, timesteps]
    return lagged_df.values.reshape((lagged_df.shape[0], n_out))


def prepare_data(data, n_in, n_out, step_foreward):
    df = pd.DataFrame(data)

    # check steps and cut data at the beginning
    timesteps = df.shape[0]
    steps = int((timesteps - n_in - n_out) / step_foreward)
    nDrop = timesteps - (steps * n_out + n_in + n_out)
    if nDrop > 0:
        df = df[nDrop:]
    return df


def create_tensors(data, column_value, n_in=1, n_out=1, step_foreward=1, dropNaN=True):
    n_features = data.shape[1]
    df = pd.DataFrame(data)

    # X tensor
    cols = list()
    dfX = df[column_value][:-n_out]
    for i in range(n_in, 0, -1):
        cols.append(data.shift(i))
    lagged_df = pd.concat(cols, axis=1)
    if dropNaN:
        lagged_df.dropna(inplace=True)
    # reshape data to shape [samples, timesteps, features]
    tensor_X = lagged_df.values.reshape((lagged_df.shape[0], n_in, n_features))
    tensor_X = tensor_X[range(0, tensor_X.shape[0], step_foreward)]

    # y tensor
    cols = list()
    dfY = df[column_value][n_in:]
    for i in range(0, n_out):
        cols.append(dfY.shift(-i))
    lagged_df = pd.concat(cols, axis=1)
    if dropNaN:
        lagged_df.dropna(inplace=True)
    # reshape data to shape [samples, timesteps]
    tensor_y = lagged_df.values.reshape((lagged_df.shape[0], n_out))
    tensor_y = tensor_y[range(0, tensor_y.shape[0], step_foreward)]

    return tensor_X, tensor_y