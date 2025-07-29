from flask import Flask, request, jsonify, render_template, redirect
from google.cloud import datastore

app = Flask(__name__)
client = datastore.Client()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/form')
def form():
    return render_template('form.html')

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

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)
