<!--If you are submitting this pull request, please fill out this section-->
**Description of changes**
<!--Summaries the changes you made as part of this pull request-->



**How to test**
<!--Any specific parts of the system that need to be tested to validate this change-->



Fixes #xxx

---

<!--Complete this section if you are the tester-->
**To test**
* Log into the devolpement nodes
* `git checkout this-pull-request-branch`
* restart services on each node (information on how to do this can be found in the development documentation)
* Submit some runs with the manualsubmission.py script

Once you are happy, merge this pull request into develop, and update the development nodes to the devlop branch
```
> git checkout origin/devlop
> git fetch -p
> git pull origin/develop
```
