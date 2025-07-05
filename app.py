from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import csv
import os
from datetime import datetime
import io
import matplotlib.pyplot as plt

app = Flask(__name__)
FILENAME = 'expenses.csv'
app.secret_key = 'your_secret_key_here'

def initialize_csv():
    if not os.path.exists(FILENAME) or os.stat(FILENAME).st_size == 0:
        with open(FILENAME, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Date', 'Category', 'Amount', 'Note'])

initialize_csv()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        date_str = request.form.get('date')
        category = request.form.get('category')
        amount_str = request.form.get('amount')
        note = request.form.get('note')

        # Validate date
        try:
            if not date_str:
                date_str = datetime.today().strftime('%Y-%m-%d')
            else:
                datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD.")
            return redirect(url_for('add_expense'))

        # Validate category
        if not category or category.strip() == '':
            flash("Category is required.")
            return redirect(url_for('add_expense'))

        # Validate amount
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except (ValueError, TypeError):
            flash("Amount must be a positive number.")
            return redirect(url_for('add_expense'))

        # Append to CSV
        with open(FILENAME, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([date_str, category, amount, note])

        flash("Expense added successfully!")
        return redirect(url_for('add_expense'))

    # GET request: show form
    today_str = datetime.today().strftime('%Y-%m-%d')
    return render_template('add_expense.html', today=today_str)

@app.route('/expenses')
def view_expenses():
    expenses = []

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    try:
        with open(FILENAME, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if start_date and end_date:
                    try:
                        row_date = datetime.strptime(row['Date'], '%Y-%m-%d').date()
                        sd = datetime.strptime(start_date, '%Y-%m-%d').date()
                        ed = datetime.strptime(end_date, '%Y-%m-%d').date()
                        if sd <= row_date <= ed:
                            expenses.append(row)
                    except ValueError:
                        continue  # skip invalid dates
                else:
                    expenses.append(row)
    except FileNotFoundError:
        pass

    return render_template('view_expenses.html', expenses=expenses, start_date=start_date, end_date=end_date)

@app.route('/delete/<int:row_index>', methods=['POST'])
def delete_expense(row_index):
    expenses = []

    # Read all expenses
    try:
        with open(FILENAME, mode='r') as file:
            reader = csv.reader(file)
            expenses = list(reader)
    except FileNotFoundError:
        flash("No expense file found.")
        return redirect(url_for('view_expenses'))

    # Check if valid index (skip header)
    if 1 <= row_index < len(expenses):
        deleted_row = expenses.pop(row_index)
        with open(FILENAME, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(expenses)
        flash(f"Deleted expense: {deleted_row}")
    else:
        flash("Invalid expense index for deletion.")

    return redirect(url_for('view_expenses'))

@app.route('/visualize/<chart_type>')
def visualize(chart_type):
    summary = {}

    try:
        with open(FILENAME, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                category = row['Category']
                try:
                    amount = float(row['Amount'])
                except (ValueError, TypeError):
                    continue

                if category in summary:
                    summary[category] += amount
                else:
                    summary[category] = amount
    except FileNotFoundError:
        flash("No expenses to visualize.")
        return redirect(url_for('index'))

    if not summary:
        flash("No expenses to visualize.")
        return redirect(url_for('index'))

    categories = list(summary.keys())
    amounts = list(summary.values())

    fig, ax = plt.subplots(figsize=(7, 5))

    if chart_type == 'pie':
        ax.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=140)
        ax.axis('equal')
        plt.title('Expense Distribution by Category')
    elif chart_type == 'bar':
        bars = ax.bar(categories, amounts, color='skyblue')
        ax.set_xlabel('Category')
        ax.set_ylabel('Total Amount')
        ax.set_title('Expenses by Category')
        plt.xticks(rotation=45)

        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, yval + 0.05, f'{yval:.2f}', ha='center', va='bottom')
    else:
        flash("Invalid chart type requested.")
        return redirect(url_for('index'))

    img = io.BytesIO()
    plt.tight_layout()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig)

    return send_file(img, mimetype='image/png')




if __name__ == '__main__':
    app.run(debug=True)
