# How to Run

![FedEx Logo](https://upload.wikimedia.org/wikipedia/commons/thumb/b/b9/FedEx_Corporation_-_2016_Logo.svg/1920px-FedEx_Corporation_-_2016_Logo.svg.png)

## Main Solution

### Enhanced Layering Approach

Place the input data in `input.txt` file in the format specified in the problem statement.\
The `input.txt` file should be next to the `main.exe` executable.\
The output will be obtained in `output.txt` file next to the `main.exe` executable.

## Other Approaches

### First Fit Approach

Same as Enhanced Layering Approach.

### Dimension Based Layering Approach and Strip Rotation and Compaction Approach

Use Python 3.9.\
Install modules in `requirements.txt`.\
Run `Dimension-Based_Layering_Algorithm.py` or `Strip_Rotation_and_Compaction_Approach.py` from Python.\
The `input.txt` file should be next to the Python script.\
The output will be obtained in `output.txt` file next to the Python script.

### Reinforcement Learning Approach

Till now only asynchronous MCTS, distributed games generation, and training loop are implemented.\
To test the code:\
Run `setup.ps1` to create a virtual environment and install all scripts.\
Run `fastapi run worker.py` to start a worker.\
Run `python train.py --worker_addresses=127.0.0.1:8000 --iteration_count=64` for games generation and training.

## Extras

### Validator

`python validate.py --input input.txt --output output.txt`

### Visualizer

Open VS Code, navigate to the Extensions view (Ctrl+Shift+X), search for "Live Server," and click Install.\
After installation, right-click the `index.html` file and select "Open with Live Server" to launch the visualization.\
You can then upload the `output.txt` file to view the 3D bin packing process.
