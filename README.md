This app will run with root permissions, so use it with caution and block this web app behind a wireguard network
I tried to do it with only wg-quick and with regular user, we can bring up wg with it but for CRUD operation against
interface without breaking other peers sessions, we should use wg terminal app it self and that app wil only run on root
i think because it uses kernel level modules and apps.
i could run this in docker with root permissions there but people should understand that docker will work correctly only
as root and that is just like out problem . we can run docker as another user but that has overheats it self.
this is just the beginning and i'm open for change in it ...

you should provide .env file in application directory, where pyproject.toml and gunicorn_conf.py is located
you can mv or rename env file in application directory to .env and fill the uncommented parameters, and uncomment
commented one for more control over application

# Development mode

1. git clone the project
2. cd to folder
3. poetry shell
4. poetry install
5. mv ./default.env ./.env (and change it to ur need)
6.  sh development.uvicorn.sh (
or run python ./backend_pre_start.py && python ./initial_data.py && .venv/bin/uvicorn wg_backend.main:app --reload --port 8000 --host localhost )  
### see localhost:8000/docs or localhost:8000/redoc   
(note): these three commands,
first will create files and directories that this app needs with their correct permissions 
second will create first superuser and first in 'db' wireguard interface from provided .env file,
third will run this app with uvicorn(a very nice server) on specified port in localhost
    
## https://docs.gunicorn.org/en/latest/deploy.html
# Production mode
#### [Systemd]
#### create a user for nginx, in nginx.conf file(user directive) and in .socket file(SocketUser attribute)
#### this user need to read /run/gunicorn.sock file and nginx config files in /etc/nginx/ directory (nginx installation will create one and you can use that for this purpose)
### example
1. sudo useradd -M -N http-user -p 'password'
#### this will create a user with name of gunicorn and no home dir and no user group with same name (you can see what this command do with 'useradd -h')
2.  sudo useradd -M -N gunicorn -p 'password' -G sudo
#### same as before but add it to sudo group 

 another user for gunicorn to actually use it for server functionality (User and Group attributes in .service file)

1. sudo mv ./prod_dir/gunicorn.service /etc/systemd/system/;
2. sudo mv ./prod_dir/gunicorn.socket /etc/systemd/system/;
3. sudo systemctl enable gunicorn (for starting after server restart)
4. sudo systemctl start gunicorn.socket && sudo systemctl start gunicorn.service
5. mv ./prod_dir/wg_backend.nginx.conf /etc/nginx/(sites-enabled or conf.d)
6. sudo nginx -s reload

: if there is a problem running app, its permission problem

# ready to go
