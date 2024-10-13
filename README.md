# NGAGE

## Overview

**NGAGE (NTT Grafana Automated Generator for Excel)** is an automation tool designed to generate Excel reports from Grafana CSV files. This project was requested by the NTT team to streamline report generation for DBS Bank. The application automates the process of reading CSV files and exporting them as formatted Excel documents, reducing manual work and increasing productivity.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Development Stage](#development-stage)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Automated CSV to Excel Conversion**: Takes Grafana CSV files as input and generates Excel reports.
- **Batch Processing**: Supports handling multiple CSV files simultaneously.
- **User-Friendly Interface**: Provides an intuitive interface for selecting and processing files.
- **Customizable Output**: Outputs Excel files with predefined templates and formatting.
- **Cross-Platform Compatibility**: Works on Windows, MacOS, and Linux.

## Prerequisites

Before using NGAGE, ensure you have the following installed:

- Python 3.7 or higher
- Required Python packages (can be installed via `requirements.txt`)
- Grafana CSV files as input

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/koetjeengdjalanan/NGAGE.git
    ```

2. Navigate to the project directory:
    ```bash
    cd NGAGE
    ```

3. Set up a virtual environment (optional but recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

4. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Once everything is set up, you can start using NGAGE to process Grafana CSV files:

1. Run the main script:
    ```bash
    python main.py
    ```

2. Select the CSV files for processing through the application interface.

3. The application will generate Excel reports based on the CSV inputs and save them to the output directory.

## Development Stage

### Wire Frame
The application is designed with a simple and efficient UI. The wireframe of the user interface is outlined in the documentation, providing a clear idea of how users interact with the app.

### User Interaction Sequence
Users upload CSV files, select the desired options for Excel output, and process the files. The app then automatically generates and formats the Excel reports.

### Logic & Algorithm

- **Open & Read File**: The app reads CSV files using Python's `pandas` library, ensuring compatibility with different formats.
- **Processing Data**:
  - `MainView.process_data()`: Handles the main processing logic, triggering the data handling and report generation.
  - `processing.process_with_from_n_to()`: Manages the conversion of specific data ranges from CSV to Excel format.
  - `processing.process_from_to()`: Finalizes the Excel export by ensuring all data is formatted and written to the output files.

## Contributing

We welcome contributions to NGAGE! Here's how you can contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix:
    ```bash
    git checkout -b feature-name
    ```
3. Make your changes and commit them:
    ```bash
    git commit -m "Description of changes"
    ```
4. Push to your branch:
    ```bash
    git push origin feature-name
    ```
5. Open a pull request, and we'll review your changes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

### Acknowledgments

This project was commissioned by NTT for DBS Bank to automate report generation and streamline operations.

