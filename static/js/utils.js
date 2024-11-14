console.log("UTILS LOADED");

function generateRadioButtons(container, rows, buttonsPerRow) {
    container.innerHTML = ''; // Clear existing buttons
    let buttonCount = 0;

    for (let row = 0; row < rows; row++) {
        const rowDiv = document.createElement('div');
        rowDiv.className = 'row mb-2';

        for (let col = 0; col < buttonsPerRow; col++) {
            if (buttonCount >= rows * buttonsPerRow) break;

            const radioWrapper = document.createElement('div');
            radioWrapper.className = 'col-md-2 form-check form-check-inline';

            const radioInput = document.createElement('input');
            radioInput.className = 'form-check-input';
            radioInput.type = 'radio';
            radioInput.name = 'sample-number';
            radioInput.id = `sample-number-${buttonCount}`;
            radioInput.value = buttonCount;
            radioInput.required = true;

            // Make the first radio button checked
            if (buttonCount === 0) {
                radioInput.checked = true;
            }

            const radioLabel = document.createElement('label');
            radioLabel.className = 'form-check-label';
            radioLabel.htmlFor = `sample-number-${buttonCount}`;
            radioLabel.textContent = `${buttonCount}`;

            radioWrapper.appendChild(radioInput);
            radioWrapper.appendChild(radioLabel);
            rowDiv.appendChild(radioWrapper);

            buttonCount++;
        }

        container.appendChild(rowDiv);
    }
}
