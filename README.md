# How to run

## Main Solution

### Enhanced Layering Approach

Place the input data in `input.txt` file in the format specified in problem statement.\
The `input.txt` file should be next to the `main.exe` executable.\
The output will be obtained in `output.txt` file next to the `main.exe` executable.

## Other Approaches

### First Fit Approach

Same as Enhanced Layering Approach

### Dimension Based Layering Approach and Strip Rotation and Compaction Approach

Use python 3.9\
Install modules in requirements.txt\
run `Dimension-Based_Layering_Algorithm.py` or `Strip Rotation_and_Compaction_Approach.py` from python.\
The `input.txt` file should be next to the python script.\
The output will be obtained in `output.txt` file next to the python script.

### Reinforcement Learning Approach

Till now only asynchonous MCTS, distributed games generation and training loop is implemented.\
To test code:\
Run `setup.ps1` to create a virutal environment and install all scripts.\
Run `fastapi run worker.py` to start a worker.\
Run `python train.py --worker_addresses=127.0.0.1:8000 --iteration_count=64` for games generation and training.

## Extras

### Validator

`python validate.py --input input.txt --output output.txt`

### Visualizer

Open VS Code, navigate to the Extensions view (Ctrl+Shift+X), search for "Live Server," and click Install.\
After installation, right-click the `index.html` file and select "Open with Live Server" to launch the visualization.\
You can then upload the `output.txt` file to view the 3D bin packing process.
