console.log("UTILS LOADED");

function calculateProcedureTime() {
    const XRD_SCAN_TIME = 2; // Base time for each XRD scan in minutes
    const RAMP_RATE = 60;    // Ramp rate is 60°C/min

    const minTemp = parseFloat($('#min-temperature').val());
    const maxTemp = parseFloat($('#max-temperature').val());
    const numScans = parseInt($('#number-of-scans').val());
    const minAngle = parseFloat($('#min-angle').val());
    const maxAngle = parseFloat($('#max-angle').val());
    const precision = $('#precision-select').val();  // Low or High precision

    if (!isNaN(minTemp) && !isNaN(maxTemp) && !isNaN(numScans) && !isNaN(minAngle) && !isNaN(maxAngle)) {
        // Calculate the ramp time for temperature change
        const rampTime = (maxTemp - minTemp) / RAMP_RATE;

        // Calculate the XRD scan time contribution based on precision
        const precisionFactor = (precision === "High") ? 1.5 : 1; // High precision takes 1.5x longer
        const scanRange = maxAngle - minAngle;  // The 2θ range
        const scanTime = XRD_SCAN_TIME * (scanRange / 100) * precisionFactor;  // Adjust scan time based on 2θ range and precision

        // Total scan time = (scan time per scan * number of scans)
        const totalScanTime = scanTime * numScans;

        // Total procedure time = scan time + ramp time
        const totalTime = totalScanTime + rampTime;

        // Breakdown of contributions
        const scanBreakdown = `${scanTime.toFixed(2)} min/scan * ${numScans} scans = ${totalScanTime.toFixed(2)} min`;
        const rampBreakdown = `${(rampTime).toFixed(2)} min ramping (60°C/min)`;

        // Display the estimated time sentence
        $('#estimated-time').text(`Estimated Procedure Time: ${(totalTime).toFixed(2)} min = ${(totalTime / 60).toFixed(2)} hr`);
        
        // Display the breakdown with proper alignment
        $('#scan-breakdown').text(scanBreakdown);
        $('#ramp-breakdown').text(rampBreakdown);

        // Show the breakdown section
        $('#time-breakdown').show();
    } else {
        $('#estimated-time').text('');
        $('#time-breakdown').hide();
    }
}

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


