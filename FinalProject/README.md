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

   **python FinalProject.py**

5. This program using Yahoo Finance to fetch Ticker data. This can sometimes time-out. Please rerun the program if it errors out. Because of limited computation power, I had to reduce the number of tickers and limit the history

6. For the given tickers, this program calculates 21 EMA and 45 EMA

7. For each of the EMA above, it calculates and upright pyramid, an inverted pyramid and a reflecting pyramid

8. For each Pyramid, it then calculates the position sizing, that is, percentage vol model, Market's money model and multiple tier position sizing.

9. It then shows KPIs for each of the portfolios

10. From the few observations after changing inputs, it looks like position sizing model has very small impact on returns. Period calulations have a bit more impact as oppose to position sizing model. But biggest impact was caused by pyramid type. It looks like inverted pyramid seems to be performing best, a bit better over upright pyramid. Reflective pyramid seems to be performing worst. (Given that we close our position after some time and markets are bullish over long period, this makes sense) 
