# PyTester: An event-driven backtester framework

## Usage:

This event driven backtester follows the general idea found in the event-driven with python tutorial found [here](https://www.quantstart.com/articles/Event-Driven-Backtesting-with-Python-Part-I/). It is developed with python queue module as a shared data bus, with 4 major components (*'engines'*):

### DataHandler : 

 channel data from csv, sql, or other sources to this engine, responsible for generating a bar data for each traded contract/stock whenever the current queue becomes empty (_which signifies the end of the processing of last bar data by the rest of the program_)

### Strategy :

 takes bar data from the queue and give out signals to be used in trading. 
 *Note*: This is a highly flexible interface so other operatiosn like generating csv data from datasource can also be done here

### Portfolio:

 takes in signal and market information, generate open order (in cash amount) and close position order (in real amount)

### Executor:

 takes in order generated by portfolio, execute it in either simulated trading environment (when next market info bar is pushed) or via a real broker account. Generate a confirmation when it is done.
 

## Development Goal:

Here, I will continue developing more stategies implemented elsewhere. Also, I will continue increasing the performance by swicthing between various data structures
 
## Performance Estimate:

As per the snakeviz analysis I run, this backtester can run 2000+ rows of backtesting of 50+ contracts at a time in under 0.1 second, which is 20-40 times faster than what I used to do using a semi-vectorized approach in pandas.
 

## Implemented Strategies:

#### Future market industrial index generator:

Calculate an industrial index based on equal weighting all future contract's daily percentage change, store it in a csv file

#### Simple Don Chian channle trading strategy
