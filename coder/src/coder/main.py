#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from coder.crew import Coder

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

assignment = "Write a python program to calculate the first 10,000 terms of this series, multiplying the total by 4: 1-1/3+1/5-1/7+1/9..."


def run():
    """
    Run the coder crew.
    """
    inputs = {
        'inputs': assignment
    }

    try:
        result = Coder().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


    print(result.raw)

if __name__ == "__main__":
    run()