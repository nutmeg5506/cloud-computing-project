from flask import Flask, request, jsonify, render_template, redirect
from google.cloud import datastore
from io import BytesIO
import base64
import matplotlib.pyplot as plt

app = Flask(__name__)
client = datastore.Client()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/analyze')
def analyze():
    return render_template('analyze.html')

@app.route('/expenses')
def expenses():
    query = client.query(kind='Expense')
    results = list(query.fetch())

    expenses_list = []
    for item in results:
        expense = dict(item)
        expense['id'] = item.key.id_or_name
        expenses_list.append(expense)
        
    expenses_list = sorted(expenses_list, key=lambda x: x['date'])
    return render_template('expenses.html', expenses=expenses_list)

@app.route('/add_expense', methods=['POST'])
def add_expense():
    data = request.get_json()

    if not data or not all(k in data for k in ('date', 'amount', 'category')):
        return jsonify({"error": "Missing required fields"}), 400

    expense = datastore.Entity(key=client.key('Expense'))
    expense.update(data)
    client.put(expense)

    return jsonify({"status": "saved", "data": data}), 201

@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    key = client.key('Expense', expense_id)
    client.delete(key)
    return redirect('/expenses')

@app.route('/analyze/date/<string:date_analyzed>', methods=['POST'])
def analyze_by_date(date_analyzed):
    query = client.query(kind='Expense')
    results = list(query.fetch())

    expenses_list = []
    for item in results:
        expense = dict(item)
        expense['id'] = item.key.id_or_name
        expenses_list.append(expense)
        
    expenses_list = sorted(expenses_list, key=lambda x: x['date'])
    dates = {}
    if date_analyzed == 'Day':
        for expense in expenses_list:
            if expense['date'] in dates:
              dates[expense['date']] += expense["amount"]
            else:
                dates[expense['date']] = expense['amount']

    elif date_analyzed == 'Month':
        for expense in expenses_list:
            month = expense['date'][0:7]
            if month in dates:
                dates[month] += expense['amount']
            else:
                dates[month] = expense['amount']

    elif date_analyzed == 'Year':
        for expense in expenses_list:
            year = expense['date'][0:4]
            if year in dates:
                dates[year] += expense['amount']
            else:
                dates[year] = expense['amount']

    plt.figure(figsize=(10, 5))
    plt.plot(dates.keys(), dates.values(), marker='o')
    plt.title(f"Expenses by {date_analyzed}")
    plt.ylabel("Amount")
    plt.xlabel(f"{date_analyzed}")
    plt.xticks(rotation=45)
    plt.tight_layout()

    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    
    return render_template('analyze_result.html', plot_url=plot_url)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
