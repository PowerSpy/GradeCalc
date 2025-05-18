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
    pattern = r'(.*?)\s+(\d+\.?\d*%)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*%)\s*([A-F][+-]?)?'
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

            if entry['score'] == 0 and entry['total'] == 0:
                percent = -1
                entry['percent'] = "-1"
                entry['grade'] = ""
            else:
                percent = round((entry['score'] / entry['total']) * 100, 2)
                entry['percent'] = f"{percent}%"
                entry['grade'] = percent_to_letter(percent)

    return jsonify(entries)

@app.route('/overallGrade', methods=['POST'])
def grade():
    data = request.get_json()
    entries = data['info']

    weighted_total = 0
    total_weight = 0

    for entry in entries:
        score = float(entry['score'])
        total = float(entry['total'])

        if score == 0 and total == 0:
            entry['percent'] = "-1"
            entry['grade'] = ""
            continue

        weight = float(entry['weight'][:-1])  # Remove % symbol
        entry['percent'] = f"{round((score / total) * 100, 2)}%"
        entry['grade'] = percent_to_letter(round((score / total) * 100, 2))

        weighted_total += (score / total) * weight
        total_weight += weight

    if total_weight == 0:
        overall_percent = 0
    else:
        overall_percent = round(100 * (weighted_total / total_weight), 2)

    return jsonify({'percent': overall_percent, 'grade': percent_to_letter(overall_percent)})

@app.route('/recalc', methods=['POST'])
def recalc():
    data = request.get_json()
    entries = data['info']

    for entry in entries:
        score = float(entry['score'])
        total = float(entry['total'])

        if score == 0 and total == 0:
            entry['percent'] = "-1"
            entry['grade'] = ""
        else:
            this_perc = round((score / total) * 100, 2)
            entry['percent'] = f"{this_perc}%"
            entry['grade'] = percent_to_letter(this_perc)

    return jsonify(entries)

@app.route('/categoryNeed', methods=['POST'])
def needed():
    data = request.get_json()
    entries = data['entry']
    mock = data['mock']  # [category, max_points, desired_overall_percent]

    target_category = mock[0]
    max_points = float(mock[1])
    desired_overall = float(mock[2].replace('%', ''))

    # Calculate total weight
    total_weight = sum(float(entry['weight'][:-1]) for entry in entries)

    # Track current weighted percent (excluding the category we're targeting)
    weighted_current = 0
    target_weight = 0
    current_score = 0
    current_total = 0

    for entry in entries:
        weight = float(entry['weight'][:-1])
        score = float(entry['score'])
        total = float(entry['total'])

        if entry['category'] == target_category:
            target_weight = weight
            current_score = score
            current_total = total
        else:
            weighted_current += (score / total) * weight

    # Normalize weights (so the weights aren't assumed to sum to 100)
    desired_weighted = (desired_overall / 100) * total_weight

    # Let x = points needed on the new assignment
    # Equation: (current_score + x) / (current_total + max_points) * target_weight + weighted_current = desired_weighted
    # Solve for x:
    denominator = current_total + max_points
    numerator = desired_weighted - weighted_current
    if target_weight == 0:
        return jsonify({"error": "Target category has 0 weight"}), 400

    required_score = ((numerator / target_weight) * denominator) - current_score

    if required_score > max_points:
        result = "Not possible"
    elif required_score < 0:
        result = 0
    else:
        result = round(required_score, 2)

    return jsonify({
        'needed_score': result,
        'category': target_category,
        'max_points': max_points,
        'desired_overall_percent': f"{desired_overall}%",
        'letter_equivalent': percent_to_letter(desired_overall)
    })

    

if __name__ == '__main__':
    app.run(port=8000, debug=True)
