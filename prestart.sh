echo "updating database model..."
sleep 5; # wait for db to be up
flask db upgrade
