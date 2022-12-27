from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from process import Process
import pandas as pd

app = Flask(__name__)
app.debug = True
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/process', methods=['POST'])
@cross_origin()
def process():
    # # Get the user input from the request body
    data = request.get_json()
    # Perform the backend processing here using the provided code
    p = Process(data,df,df_xl)
    plot_quanto = p.plot()
    # Return the output as a JSON response
    return plot_quanto





if __name__ == '__main__':
    df = pd.read_csv('SA_Price.csv', parse_dates=['Dates'],index_col='Dates')
    # Adding date col
    df['Only Date'] = df.index.date
    df['Only Date'] = pd.to_datetime(df['Only Date'])
    df_xl = pd.read_excel('Parafield_TMAX.xlsx',index_col='Date')
    app.run()
