## README

1. This program was created using Anaconda2 v4.4.0. However, this should
work on any standard installations of python 2.7.x+
2. To install the packages required to run the program, please find the
requirements.txt file. This file contains all the packages used by the
program. To install, do the following:

    **pip install -r requirements.txt**
3. The program was developed on a flavour of Windows (Windows 10). The code tends to be
cross-platform, however this has not been tested on a Linux or Mac
machine.

4. The program is launched by typing the following on the command line:

   **python a5.py**

5. The following program prompts the user for stock ticker, and fetches data from Yahoo Finance

6. Accepts standard SnP500 Tickers. Other tickers for countries haven't been tried.
If they would work, they would have to be prefixed with their Stock Exchange. Please refer to
Yahoo Finance for more details

7. It then devises a trading strategy based on the Mean Reversion and breakout obtained in the above step.

8. It then calculates an upright pyramid, and optimal f (for 80% in-sample data) for both the strategies.

9. Shows KPI for 20% out-of-sample data
