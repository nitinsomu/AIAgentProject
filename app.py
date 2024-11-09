from flask import Flask, request, render_template, jsonify
import os
import pandas as pd
from groq import Groq
import requests
from serpapi import GoogleSearch
from dotenv import load_dotenv
import re

app = Flask(__name__)

load_dotenv()
SERP_API_KEY = os.getenv("SERP_API_KEY")

client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
)

df = pd.DataFrame()
columns = []
# Home page
@app.route('/')
def index():
    return render_template('index.html')

# File upload route
@app.route('/upload', methods=['POST'])
def upload_file():
    global df
    global columns
    file = request.files['file']
    if file:
        df = pd.read_csv(file, header=0)
        columns = df.columns.tolist()
        return render_template('index.html', columns=columns)

# Query Route
@app.route('/query', methods=['POST'])
def query():
    mainQuery = request.form['query']
    column = request.form['column']
    mainResults = []
    for element in df[column]:
        query = re.sub(r'\{.*?\}', element, mainQuery)
        params = {
        "engine": "google",
        "q": query,
        "hl": "en",
        "num": "10",
        "api_key": SERP_API_KEY
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        organic_results = results["organic_results"]
        results_string = " ".join(map(str, organic_results))
        groqQuery = query + column + "Give me the answer in one word. If there are multiple answers output the first that appears. If there is no answer, output - Not Available. Make sure only one word is generated and nothing else. If the answer is numerical value output the number and the unit, if there is one"
        results_string += groqQuery
        chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": results_string,
            }
        ],
        model="llama3-70b-8192",
        )
        mainResults.append([element, chat_completion.choices[0].message.content])

    return render_template('index.html', column = column, query = query, results = mainResults, columns = columns)
    


if __name__ == '__main__':
    app.run(debug=True)
