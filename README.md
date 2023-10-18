# SmartWave Debugging Python API

This Python API is designed to simplify the process of debugging the SmartWave FPGA by offering features for 
testing and analyzing the SmartWave's performance.

## Requirements

To get started with this API, please ensure you follow these requirements:

1. **IDE Selection:** 
I recommend using PyCharm as your IDE for this project. 
PyCharm offers seamless integration with GitHub repositories, making version control and 
collaboration a lot easier. If you are new to PyCharm or need assistance setting it up with GitHub, 
you can refer to this helpful guide: 
[How to Manage Projects Hosted on GitHub with PyCharm](https://www.jetbrains.com/help/pycharm/manage-projects-hosted-on-github.html#clone-from-GitHub).

   If you are having issues psuhing back to your remote branch, go to 
`File -> Settings -> Version Control -> Git` and at the bottom, tick the **User credential helper**  


2. **Virtual Environment Setup:** 
It's essential to configure your virtual environment correctly within PyCharm. 
You can do this when starting a new project or by navigating to 
`File -> Settings -> Project -> Project Interpreter`. 
I recommend using Python 3.11 as the current version of Python 3.12 has a known bug that may 
cause issues during package installations.


3. **Install Python Packages:** 
Once your virtual environment is set up, make sure to install all the required Python packages listed in the 
`requirements.txt` file. You can easily achieve this by running the following command in your terminal:

   ```bash
   pip install -r requirements.txt
   ```

4. **Formatting:**
Follow the PEP-8 guidelines for code readability and consistency. Maintaining a consistent style across branches is 
essential.
Prior to merging your branch back to the master, make sure your code is free from **mypy** and **pylint** errors. This helps 
maintain code quality and correctness.
