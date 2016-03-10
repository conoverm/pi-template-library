#!/bin/bash

NAME="template_library"            # Name of the application
APPDIR=/apps/template_library         # Project directory
SOCKFILE=/tmp/template_library.sock    # we will communicte using this unix socket
USER=cstech                 # the user to run as
GROUP=cstech                # the group to run as
NUM_WORKERS=3               # how many worker processes should Gunicorn spawn
TIMEOUT=600                 # how long gunicorn workers process until terminated

# Create a secret key if in prod
if [[ $RUN_LEVEL == 'prod' ]] || [[ $RUN_LEVEL == 'qa' ]]; then
	export SECRET_KEY="$(python -c 'import os; print os.urandom(64)')"
fi

echo "Starting $NAME as `whoami`"

# Activate the virtual environment
cd $APPDIR
source venv/bin/activate

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start your Unicorn
# Programs meant to be run under supervisor should not daemonize themselves
# (so do not use --daemon)
exec venv/bin/gunicorn ${NAME}:app \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --log-level=debug \
  --bind=unix:$SOCKFILE \
  --timeout $TIMEOUT \
  2>&1
