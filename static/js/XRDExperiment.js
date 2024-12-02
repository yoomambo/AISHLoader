class XRDExperiment {
    constructor(min2theta, max2theta, precision, minTemp, maxTemp, numScans) {
        this.xrdparams = {
            min2theta: min2theta,
            max2theta: max2theta,
            precision: precision
        };

        this.heatingparams = {
            minTemp: minTemp,
            maxTemp: maxTemp,
            numScans: numScans
        };
    }
}