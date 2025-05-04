from flask import Flask, request, jsonify, send_from_directory
import re

app = Flask(__name__, static_folder='.')

def percent_to_letter(percent):
    if percent >= 98:
        return "A+"
    elif percent >= 93:
        return "A"
    elif percent >= 90:
        return "A-"
    elif percent >= 87:
        return "B+"
    elif percent >= 83:
        return "B"
    elif percent >= 80:
        return "B-"
    elif percent >= 77:
        return "C+"
    elif percent >= 73:
        return "C"
    elif percent >= 70:
        return "C-"
    elif percent >= 63:
        return "D"
    elif percent > 60:
        return "D-"
    else:
        return "F"

@app.route('/')
def index():
    return send_from_directory('.', 'main.html')

@app.route('/submit', methods=['POST'])
def submit():
    data = request.form.get('entry', '')

    clean_data = ' '.join(data.split())
    pattern = r'(.*?)\s+(\d+\.?\d*%)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*%)\s+([A-F][+-]?)'
    matches = re.findall(pattern, clean_data)

    results = [
        {
            'category': cat.strip(),
            'weight': w,
            'score': s,
            'total': t,
            'percent': pct,
            'grade': grade
        }
        for (cat, w, s, t, pct, grade) in matches
    ]
    return jsonify(results)

@app.route('/newData', methods=['POST'])
def update():
    data = request.get_json()
    entries = data['entry']
    newdata = data['update']


    category = newdata[0]

    for entry in entries:
        if entry['category'] == category:
            entry['score'] = float(entry['score']) + float(newdata[1])
            entry['total'] = float(entry['total']) + float(newdata[2])


            percent = round((entry['score'] / entry['total']) * 100, 2)
            entry['percent'] = f"{percent}%"

            entry['grade'] = percent_to_letter(percent)

    return jsonify(entries)

@app.route('/overallGrade', methods=['POST'])
def grade():
    data = request.get_json()
    entries = data['info']

    percent = 0

    for entry in entries:
        this_perc_as_decimal = round(float(entry['score']) / float(entry['total']), 4)
        this_perc = round(100 * (float(entry['score']) / float(entry['total'])), 2)
        entry['percent'] = f"{this_perc}%"
        entry['grade'] = percent_to_letter(this_perc)
        percent += this_perc_as_decimal * float(entry['weight'][:-1])
    
    return jsonify({'percent' : percent, 'grade' : percent_to_letter(percent)})

@app.route('/recalc', methods=['POST'])
def recalc():
    data = request.get_json()
    entries = data['info']

    for entry in entries:
        this_perc = round(100 * (float(entry['score']) / float(entry['total'])), 2)
        entry['percent'] = f"{this_perc}%"
        entry['grade'] = percent_to_letter(this_perc)
    
    return jsonify(entries)


if __name__ == '__main__':
    app.run(port=8000, debug=True)
