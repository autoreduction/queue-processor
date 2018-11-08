## clients

The client classes are a layer of abstraction between autoreduction and its external services
(Data catalog, Queue, Database) and offer a common interface for interacting with them.

![](client_class_diagram.PNG)

All clients must inherit from the AbstractClient which has functions for the required operations
for all services in autoreduction:
 * `__init__(credentials)`
   * Validate and cache the credentials for connecting to the service.
   *See `utils.clients.settings` module for more details on `ClientSettings`.*
 * `connect()` - *abstract*
   * Connect to the service using the credentials provided in `__init__`.
 * `disconnect()` - *abstract*
   * Disconnect from the service.
 * `_test_connection()` - *abstract*
   * Return True/False to represent if the client currently has an open valid connection to the service.

Sub classes `QueueClient`, `ICATClient` and `DatabaseClient` have additional functions for service specific functionality.
For example the QueueClient has functions to serialise and send data to a queue.

A custom `ConnectionException` is used to wrap service specific connection errors into an expected exception type.
