## Option Entry Timing Analysis

This project provides a data-driven framework for identifying optimal entry points for selling put options, based on historical stock price movements and short-term reversal probabilities.

## Features

- Quantifies continuous drop durations and cumulative losses
- Computes historical distribution of price drops
- Analyzes relationship between daily drops and next-day reversals
- Evaluates "drop fermentation" (e.g., how often a 5% drop leads to a 10% drop)

## Use Cases

Helps option sellers:
- Avoid entering too early during flat or minor pullbacks
- Better allocate position sizes based on empirical probabilities
- Gain confidence ("peace of mind") from historical context

## How to Use

1. Install required packages:

   ```bash
   pip install -r requirements.txt
