# Deploying Code Changes Autoreduction
#### Development Machines
When the changes have been pushed on the `develop` branch you can pull the latest code onto the development machines by using `git pull`. You may want to `diff settings.py settings.py.template` to see if there have been any changes made to the settings file. Then it's just a case of restarting the service.

#### Production Machines
Changes to production are done in the same way except we use the `master` branch.

## Restarting services
##### Queue processors 
To restart the queue processors run 
```
./restart.sh 
```
- Check the restart has been sucessful by `ps aux | grep python` and checking the logs for activity.
##### End of run monitor
- Restart the 'Autoreduce Instrument Montior' service in the Services Control Panel.
  - Alternatively, this can be done by running `python ISIS_monitor_win_service.py [start|restart|stop]`
- Check the restart has been sucessful by checking the log.

##### Web app 
- Restart Apache
- Open the web browser to check the web app is running
