# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
# Pull in stable mantid release
FROM mantidproject/mantid

# Make the .mantid file in the root directory to store the properties file
RUN mkdir /root/.mantid ; \

# Copy the Mantid.user.properties file into the expected location in the container
COPY Mantid.user.properties /root/.mantid/Mantid.user.properties

# Run mantidpython with the autoreduction reduce.py script
# INSTRUMENT, INPUT_FILE and OUTPUT_DIR should all be passed as environment variables to the Dockerfile at runtime
CMD /opt/Mantid/bin/mantidpython "$SCRIPT" "$INPUT_FILE" "$OUTPUT_DIR" "$REDUCE_VARS"
