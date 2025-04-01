document.getElementById("analyzeButton").addEventListener("click", function() {
    const url = document.getElementById("examUrl").value;  // Get URL from input

    console.log("Fetching data from URL:", url);  // Log URL to check if it's correct

    // Send a POST request to the Flask server with the URL
    fetch('http://127.0.0.1:5000/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: url })
    })
    .then(response => response.json())
    .then(data => {
        if (data.marks_data) {
            displayResult(data.marks_data);  // Call a function to display the result
        } else {
            console.error('Error:', data.error);
        }
    })
    .catch(error => {
        console.error('Error fetching the result:', error);
    });
});

function displayResult(marksData) {
    let resultTable = document.getElementById("resultTable");
    resultTable.innerHTML = '';  // Clear any previous results

    // Create table headers
    let headerRow = document.createElement('tr');
    let headers = ['Subject', 'Attempted', 'Not Attempted', 'Correct', 'Wrong', 'Marks'];
    headers.forEach(header => {
        let th = document.createElement('th');
        th.textContent = header;
        headerRow.appendChild(th);
    });
    resultTable.appendChild(headerRow);

    // Create rows from the marksData
    marksData.forEach(item => {
        let row = document.createElement('tr');
        for (const key in item) {
            let td = document.createElement('td');
            td.textContent = item[key];
            row.appendChild(td);
        }
        resultTable.appendChild(row);
    });
}
