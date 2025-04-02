from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

app = Flask(__name__, static_folder='static')
CORS(app)

# Selenium setup
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# API endpoint to analyze exam results
@app.route('/analyze', methods=['POST'])
def analyze_exam_result():
    try:
        # Get the URL from the request
        data = request.get_json()
        url = data.get('url')

        if not url:
            return jsonify({"error": "URL is required"}), 400

        # Use Selenium to load JavaScript-rendered pages
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(url)
        html_content = driver.page_source
        driver.quit()  # Close the driver after fetching the page

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Initialize data structure
        result_data = {
            "Candidate Details": {}, 
            "Results": {
                "Sections": {},
                "Total": {
                    "Correct": 0,
                    "Wrong": 0,
                    "Attempted": 0,
                    "Marks": 0,
                    "Max Marks": 200
                }
            }
        }

        # Extract candidate details
        candidate_table = soup.find('table')
        if candidate_table:
            for row in candidate_table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) == 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    result_data["Candidate Details"][key] = value

        # Exam sections
        sections = [
            {"name": "General Intelligence and Reasoning", "range": (1, 25)},
            {"name": "General Awareness", "range": (26, 50)},
            {"name": "Quantitative Aptitude", "range": (51, 75)},
            {"name": "English", "range": (76, 100)}
        ]

        # Initialize section-wise results
        for section in sections:
            result_data["Results"]["Sections"][section["name"]] = {
                "Correct": 0,
                "Wrong": 0,
                "Attempted": 0,
                "Marks": 0
            }

        # Process questions
        question_panels = soup.find_all('div', class_='question-pnl')

        for i, panel in enumerate(question_panels, 1):
            current_section = next((s["name"] for s in sections if s["range"][0] <= i <= s["range"][1]), None)
            if not current_section:
                continue

            status_table = panel.find('table', class_='menu-tbl')
            if not status_table:
                continue

            status_td = status_table.find('td', text='Status :')
            if status_td:
                status_element = status_td.find_next_sibling('td')
                status = status_element.text.strip() if status_element else "Unknown"
            else:
                status = "Unknown"

            if status == 'Answered':
                chosen_option_td = status_table.find('td', text='Chosen Option :')
                if not chosen_option_td:
                    continue

                chosen_option_element = chosen_option_td.find_next_sibling('td')
                chosen_option = chosen_option_element.text.strip() if chosen_option_element else None

                options = panel.find_all('td', class_=['rightAns', 'wrngAns'])
                for option in options:
                    option_text = option.get_text(strip=True)
                    if chosen_option and option_text.startswith(f"{chosen_option}."):
                        if 'rightAns' in option.get('class', []):
                            result_data["Results"]["Total"]["Correct"] += 1
                            result_data["Results"]["Sections"][current_section]["Correct"] += 1
                        else:
                            result_data["Results"]["Total"]["Wrong"] += 1
                            result_data["Results"]["Sections"][current_section]["Wrong"] += 1
                        break

        # Calculate marks
        for section in sections:
            sec = result_data["Results"]["Sections"][section["name"]]
            sec["Attempted"] = sec["Correct"] + sec["Wrong"]
            sec["Marks"] = (sec["Correct"] * 2) - (sec["Wrong"] * 0.5)

        total = result_data["Results"]["Total"]
        total["Attempted"] = total["Correct"] + total["Wrong"]
        total["Marks"] = (total["Correct"] * 2) - (total["Wrong"] * 0.5)

        return jsonify(result_data)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Network error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Processing error: {str(e)}"}), 500

# Serve frontend files
@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(debug=True)
