const queueList = document.getElementById('queue-list');
const queueForm = document.getElementById('queue-form');
const itemNameInput = document.getElementById('item-name');
const sampleNumberInput = document.getElementById('sample-number');
const runningItemDiv = document.getElementById('running-item');
const startButton = document.getElementById('queue-start-button');

// Array to hold the queue items
let queueItems_array = [];

// Initialize SortableJS on the queue list
const sortable = new Sortable(queueList, {
    animation: 150,
    ghostClass: 'sortable-ghost',
    onEnd: function (evt) {
        const movedItem = queueItems_array.splice(evt.oldIndex, 1)[0]; // Remove the item from the old index
        queueItems_array.splice(evt.newIndex, 0, movedItem);          // Insert it at the new index
        renderQueue(); // Re-render the queue to reflect changes
    }
});

// Function to render the queue items in the sortable list
function renderQueue() {
    queueList.innerHTML = ''; // Clear the list before rendering

    // For each of the items in the queue list, make a queue item and add it to the sortable list
    queueItems_array.forEach((item, index) => {
        const listItem = document.createElement('li');
        listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
        listItem.innerHTML = `
                <div class="flex-grow-1">
                    <span class="item-name">${item.itemName}</span><br>
                    <span class="item-details">Sample Number: ${item.sampleNumber} ${item.optionsText}</span>
                </div>
            `;

        // Create delete button
        const deleteButton = document.createElement('button');
        deleteButton.className = 'btn btn-danger btn-sm';
        deleteButton.textContent = 'X';
        deleteButton.onclick = function () {
            queueItems_array.splice(index, 1); // Remove item from queue
            renderQueue(); // Re-render the queue
        };

        listItem.appendChild(deleteButton);
        queueList.appendChild(listItem);
    });
}

document.getElementById('queue-form').addEventListener('submit', function (event) {
    event.preventDefault();

    const itemName = itemNameInput.value.trim();
    const sampleNumber = document.querySelector('input[name="sample-number"]:checked');
    const selectedOptions = Array.from(document.querySelectorAll('input[name="options"]:checked'))
        .map(option => option.value);

    if (!itemName || !sampleNumber) {
        alert('Please fill out all fields.');
        return;
    }

    const optionsText = selectedOptions.length ? `Options: ${selectedOptions.join(', ')}` : '';
    const newItem = {
        itemName: itemName,
        sampleNumber: sampleNumber.value,
        optionsText: optionsText
    };

    queueItems_array.push(newItem); // Add new item to the queue
    renderQueue(); // Render the updated queue

    // Clear the input fields
    itemNameInput.value = '';
    sampleNumber.checked = false;
    document.querySelectorAll('input[name="options"]:checked').forEach(option => option.checked = false);
});

startButton.addEventListener('click', function () {
    if (queueItems_array.length > 0) {
        const currentItem = queueItems_array.shift(); // Remove the first item from the queue
        runningItemDiv.innerHTML = `
                <div class="flex-grow-1">
                    <span class="item-name">${currentItem.itemName}</span><br>
                    <span class="item-details">Sample Number: ${currentItem.sampleNumber} ${currentItem.optionsText}</span>
                </div>
            `; // Display in Currently Running box
        renderQueue(); // Re-render the queue to reflect changes
    } else {
        alert('No items in the queue to start.');
    }
});

// Manual Loading
document.getElementById('manualControl-autoLoadForm').addEventListener('submit', function (event) {
    event.preventDefault();

    // Get the sample number from the selected radio button
    const sampleNumber = document.querySelector('input[name="sample-number"]:checked').value;

    //Send a flask post request to the server
    fetch(`/api/load_sample?${sampleNumber}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
    });
});

// Manual Unloading
document.getElementById('manualControl-unloadButton').addEventListener('click', function () {
    //Send a flask post request to the server
    fetch('/api/unload_sample', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
    });
});

document.addEventListener('DOMContentLoaded', function () {
    // Initialize tooltips for all elements with data-bs-toggle="tooltip"
    var tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });
});