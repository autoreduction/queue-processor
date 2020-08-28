# Logger Utility

This file describes the usage of logging utilities

## log_handler.py

The log handler is a utility script to be used when logging. The `GetLogger` class can be used as a 
direct replacement for the `logging` module.

This package aims to centralise logging, enforce a standard logging format and allow configuring of 
logger on call to set:  log level; output file location; and toggle streaming of logs to the 
terminal.

### Parameters & Usage

```python
GetLogger(log_level, log_file_name, print_to_console)
```

* log_level: 
    * Description: The level of exception to log
    * Type: string
    * Default value: "DEBUG""
* log_file_name:
    * Description: File name of the log file
    * Type: string
    * Default value: `callers_filename.log`
* stream_log:
    * Description: Toggle streaming of logs to CLI
    * Type: Bool (True False)
    * Default value: False
    
Basic usage:
```python
from utils.logger.log_handler import GetLogger

logger = GetLogger(stream_log=True, log_level="DEBUG", log_file_name='logs/test.log').logger

def func(a, b, c):
    answer = a + b + c
    logger.debug(f"Answer is: {answer}")
    logger.error(f"Answer is not: {answer+1}")
    return answer

func(1, 2, 3)

logger.debug(f"Adding: {20} + {10} = {20 + 10}")
logger.debug(f"Adding: {10} + {10} = {10 + 10}")

```