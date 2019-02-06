#!/usr/bin/env bash

PKG=testserver
SERVER_DIR="/home/ec2-user/$PKG"
WEB_DIR="/var/www/$PKG"
VENV="$SERVER_DIR/venv"
PIP="$VENV/bin/pip"
PYTHON="$VENV/bin/python"
GUNICORN="$VENV/bin/gunicorn"
SUPERVISORD="$VENV/bin/supervisord"
SUPERVISORD_CONF=/etc/supervisord.conf
SOCKFILE="$WEB_DIR/$PKG.sock"
LISTEN_PORT=3000
TEST_PORT=80

sudo yum update -y
# Old AL2012
#sudo yum install -y python-pip python-devel nginx gcc
sudo yum install -y python-pip python-devel gcc
sudo sh -c "yes | amazon-linux-extras install nginx1.12"

sudo pip install --upgrade pip
sudo pip install virtualenv

sudo mkdir -p $WEB_DIR
sudo chown ec2-user $WEB_DIR

mkdir $SERVER_DIR
virtualenv $VENV
$PIP install flask gunicorn supervisor

cat <<EOF > "$SERVER_DIR/main.py"
from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def index():
    return 'Hello world'

@app.route("/echo", methods=['GET', 'POST'])
def echo():
    return request.values.get('data')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=$TEST_PORT)
EOF

cat <<EOF > "$SERVER_DIR/wsgi.py"
"""Exposes the ``app`` variable for Gunicorn"""
from main import app as application

if __name__ == "__main__":
    application.run()
EOF

cat <<EOF > "$SERVER_DIR/start-server-debug"
#!/usr/bin/env bash
sudo $GUNICORN --bind 0.0.0.0:$TEST_PORT wsgi
EOF

chmod 755 "$SERVER_DIR/start-server-debug"

cat <<EOF > "$SERVER_DIR/start-gunicorn"
#!/usr/bin/env bash
$GUNICORN \
    --bind=unix:$SOCKFILE \
    --workers 3 \
    --pid $SERVER_DIR/gunicorn.pid \
    wsgi
EOF

chmod 755 "$SERVER_DIR/start-gunicorn"

cat <<EOF > "$SERVER_DIR/supervisord.conf"
[supervisord]
logfile = $SERVER_DIR/supervisor.log
logfile_maxbytes = 10MB
logfile_backups = 1
pidfile = $SERVER_DIR/supervisor.pid
nodaemon = false

[program:$PKG]
command = $SERVER_DIR/start-gunicorn
directory = $SERVER_DIR/
stdout_logfile = $SERVER_DIR/supervisor.gunicorn.log
stdout_logfile_maxbytes = 10MB
stdout_logfile_backups = 1
redirect_stderr = true
environment=LANG=en_US.UTF-8,LC_ALL=en_US.UTF-8
user = ec2-user
EOF

sudo cp "$SERVER_DIR/supervisord.conf" $SUPERVISORD_CONF

cat <<EOF > "$SERVER_DIR/$PKG.nginx.conf"
upstream $PKG {
    server unix:$SOCKFILE fail_timeout=0;
}

server {
    listen $LISTEN_PORT default_server;
    server_name localhost;

    access_log $SERVER_DIR/nginx-access.log;
    error_log $SERVER_DIR/nginx-error.log;

    location / {
        # an HTTP header important enough to have its own Wikipedia entry:
        #   http://en.wikipedia.org/wiki/X-Forwarded-For
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;

        # pass the Host: header from the client right along so redirects
        # can be set properly within the application
        proxy_set_header Host \$http_host;

        # Don't want nginx trying to do something clever with redirects
        proxy_redirect off;

        proxy_pass http://$PKG/;
    }
}
EOF

sudo cp "$SERVER_DIR/$PKG.nginx.conf" /etc/nginx/conf.d/$PKG.conf

# Start supervisord
sudo $SUPERVISORD -c $SUPERVISORD_CONF

# Add the nginx user to the ec2-user group, so that it can read/write the socket files (owned by ec2-user)
sudo usermod -a -G ec2-user nginx

# Start nginx
sudo service nginx start

# examples
# curl localhost:3000
# curl localhost:3000/echo --data 'data=hi everybody'
