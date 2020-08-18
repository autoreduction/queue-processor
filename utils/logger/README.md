# Logger Utility

This file describes the usage of logging utilities

## log_handler.py

The log handler is a utility script to be used when logging. The GetLogger class can used as a 
direct replacement for the `logging` module.

### Parameters & Usage:

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
logger = GetLogger().logger
logger.logger.info(f"Adding: {6} + {10} = {6 + 10}")
```

## log_decorator.py
The log class decorator can be used similarly to the log handler. The log decorator is a decorator 
to place on methods which you wish to log.

### Parameters & Usage:

```python
@LogDecorator(logger, log_level, log_file_name, stream_log)
```

* logger:
    * Logger object
* log_leveL:
    * Description: The level to log at
    * Type: string
    * Default value: None
* log_file_name:
    * Description: Name of log file
    * Type: string
    * Default value: None
* stream_log:
    * Description: Toggle streaming of logs to CLI
    * Type: Bool (True, False)
    * Default value: None

Basic Usage
```python
from utils.logger.log_decorator import LogDecorator
from utils.logger.log_handler import GetLogger

logger = GetLogger()

@LogDecorator(logger=logger, stream_log=True)
def func(a, b, c):
    answer = a + b + c
    return answer
```
