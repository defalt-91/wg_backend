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