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

#shows the saved expenses ordered by date
@app.route('/expenses')
def expenses():
    #retrieves the saved expenses from Datastore
    query = client.query(kind='Expense')
    results = list(query.fetch())

    expenses_list = []

    #converts the JSON fetched from the database into a dictionary, adds the element id and appends to an expenses list
    for item in results:
        expense = dict(item)
        expense['id'] = item.key.id_or_name
        expenses_list.append(expense)

    #sorts the list by date    
    expenses_list = sorted(expenses_list, key=lambda x: x['date'])
    return render_template('expenses.html', expenses=expenses_list)

#adds more expenses to the database
@app.route('/add_expense', methods=['POST'])
def add_expense():
    data = request.get_json()

    #checks if there was data submitted through the form.html, returns an error if there is something missing
    if not data or not all(k in data for k in ('date', 'amount', 'category')):
        return jsonify({"error": "Missing required fields"}), 400

    #creates a datastore entity with the new data and saves it into the database
    expense = datastore.Entity(key=client.key('Expense'))
    expense.update(data)
    client.put(expense)

    return jsonify({"status": "saved", "data": data}), 201

#deletes the specified expense by their id
@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    key = client.key('Expense', expense_id)
    client.delete(key)
    return redirect('/expenses')

#visualizes the data with a line graph. It can be by day, month or year
@app.route('/analyze/date/<string:date_analyzed>', methods=['POST'])
def analyze_by_date(date_analyzed):
    #retrieves the data just like in the expenses function
    query = client.query(kind='Expense')
    results = list(query.fetch())

    expenses_list = []
    for item in results:
        expense = dict(item)
        expense['id'] = item.key.id_or_name
        expenses_list.append(expense)
        
    expenses_list = sorted(expenses_list, key=lambda x: x['date'])

    dates = {} #dictionary to store the total amount by dates

    #checks if the user wants to analyze the data by day, month, or year
    if date_analyzed == 'Day':
        for expense in expenses_list:
            if expense['date'] in dates:
              dates[expense['date']] += expense["amount"] #adds the amount to the total for that date
            else:
                dates[expense['date']] = expense['amount'] #initializes the dictionary with the date as the key and the first amount seen

    elif date_analyzed == 'Month':
        for expense in expenses_list:
            month = expense['date'][0:7] #slices the stored date so that it only shows year and month. Stored dates are in the form YYYY-MM-DD. Used to analyze only the months
            if month in dates:
                dates[month] += expense['amount']
            else:
                dates[month] = expense['amount']

    elif date_analyzed == 'Year':
        for expense in expenses_list:
            year = expense['date'][0:4] #slices the stored date so that it only shows the year. Used to analyze only the years
            if year in dates:
                dates[year] += expense['amount']
            else:
                dates[year] = expense['amount']

    #plots the data in a line graph
    plt.figure(figsize=(10, 5))
    plt.plot(dates.keys(), dates.values(), marker='o')
    plt.title(f"Expenses by {date_analyzed}")
    plt.ylabel("Amount")
    plt.xlabel(f"{date_analyzed}")
    plt.xticks(rotation=45)
    plt.tight_layout()

    #stores the graph as an image to send to the html. Saves it in-memory so that is doesn't save anything to the local disk
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    
    return render_template('analyze_result.html', plot_url=plot_url)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
