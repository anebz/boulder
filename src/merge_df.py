import os
import json
import pandas as pd

if __name__ == "__main__":
    prev_df = pd.read_csv('boulderdata.csv')
    temp_df = pd.read_csv('output.csv')

    if not temp_df.empty:
        df = temp_df.append(prev_df)
        df.to_csv('boulderdata.csv', index=False)
    os.remove('output.csv')
