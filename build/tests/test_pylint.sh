#!/bin/sh

errorThreshold=1100

sourceRoot=$(git rev-parse --show-toplevel)
currentDir=$(pwd)

# We have to trick pylint into thinking the entire project is a module
cd $sourceRoot

fileCount=0
errCount=0
errScore=0 # Pylint score

logFileName="pylint.log"
rm -f "$logFileName" || true

for i in $(find . -name '*.py');
do
    fileCount=$((fileCount+1))

    # Print the filename for user convinence
    echo "$i" | tee -a "$logFileName"
    output=$(pylint "$i" -f colorized -sn)
    
    # Get exit code which indicates if there were any warnings or errors
    resultCode=$?
    errScore=$((errScore+$resultCode))

    # Echo out the result
    echo $output | tee -a $logFileName

    if [ $resultCode != 0 ];
    then
        errCount=$((errCount+1))
    fi
done

echo "Processed: $fileCount"
echo "Errored: $errCount"
echo "Score: $errScore"

if [ "$errScore" -gt "$errorThreshold" ];
then
    echo "Pylint has regressed. Previous score was: $errorThreshold \nPlease fix the new warnings and retry."
    exit 1
fi

if [ "$errScore" -lt "$errorThreshold" ];
then
    echo "Pylint has improved. Please adjust the threshold to: $errScore"
    exit 1
fi

exit 0
