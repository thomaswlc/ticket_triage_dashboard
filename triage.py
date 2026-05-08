import pandas as pd

def load_data(file):
    df = pd.read_csv(file)
    return df