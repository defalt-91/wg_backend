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
3. install poetry with "curl -sSL https://install.python-poetry.org | python3 -"
4. poetry shell
5. poetry install
6. rename the default.env file with: mv ./default.env ./.env (and change it to ur need)
7. poetry run dev (for development environment)
8. poetry run prod (for production mode environment)
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

* this will create a user with name of gunicorn and no home dir and no user group with same name (you can see what this command do with 'useradd -h')

2. sudo useradd -M -N gunicorn -p 'password' -G sudo

#### same as before but add it to sudo group

another user for gunicorn to actually use it for server functionality (User and Group attributes in .service file)
* you should change DIST_DIR=/, DEBUG=false,LOG_LEVEL=WARNING or ERROR in .env file. but app will work in prod mode with just DEBUG=false, it will save it files under '${project-dir}/dist/production' folder and its LOG_LEVEL will be INFO  
1. sudo mv ./prod_dir/gunicorn.service /etc/systemd/system/;
2. sudo mv ./prod_dir/gunicorn.socket /etc/systemd/system/;
3. sudo systemctl enable gunicorn (for starting after server restart)
4. sudo systemctl start gunicorn.socket && sudo systemctl start gunicorn.service
5. mv ./prod_dir/wg_backend.nginx.conf /etc/nginx/(sites-enabled or conf.d)
6. sudo systemctl restart nginx

* if there is a problem running app, its permission problem

# ready to go


## Extra
[//]: #
    wg genkey | tee privatekey | wg pubkey > publickey

[//]: #
    wg genkey | tee /dev/stderr | wg pubkey

#### [used iptables rules]

[//]:#
    [TABLE]
    -t, --table table
          This option specifies the packet matching table which the command should operate on.  If the kernel is configured with auto‐
          matic module loading, an attempt will be made to load the appropriate module for that table if it is not already there.
    
          The tables are as follows:
    
          filter:
              This  is  the  default table (if no -t option is passed). It contains the built-in chains INPUT (for packets destined to
              local sockets), FORWARD (for packets being routed through the box), and OUTPUT (for locally-generated packets).
    
          nat:
              This table is consulted when a packet that creates a new connection is encountered.  It consists of four built-ins: PRE‐
              ROUTING (for altering packets as soon as they come in), INPUT (for altering packets destined for local sockets),  OUTPUT
              (for  altering  locally-generated packets before routing), and POSTROUTING (for altering packets as they are about to go
              out).  IPv6 NAT support is available since kernel 3.7.
    
          mangle:
              This table is used for specialized packet alteration.  Until kernel 2.4.17 it had two built-in chains:  PREROUTING  (for
              altering  incoming  packets  before  routing) and OUTPUT (for altering locally-generated packets before routing).  Since
              kernel 2.4.18, three other built-in chains are also supported: INPUT (for packets coming into the box  itself),  FORWARD
              (for altering packets being routed through the box), and POSTROUTING (for altering packets as they are about to go out).
    
          raw:
              This  table  is  used mainly for configuring exemptions from connection tracking in combination with the NOTRACK target.
              It registers at the netfilter hooks with higher priority and is thus called before ip_conntrack, or any other IP tables.
              It provides the following built-in chains: PREROUTING (for packets arriving via any network interface) and  OUTPUT  (for
              packets generated by local processes).
    
          security:
              This  table  is  used  for  Mandatory  Access  Control  (MAC) networking rules, such as those enabled by the SECMARK and
              CONNSECMARK targets.  Mandatory Access Control is implemented by Linux Security Modules such as SELinux.   The  security
              table  is  called  after  the filter table, allowing any Discretionary Access Control (DAC) rules in the filter table to
              take effect before MAC rules.  This table provides the following built-in chains: INPUT (for packets coming into the box
              itself), OUTPUT (for altering locally-generated packets before routing), and FORWARD (for altering packets being  routed
              through the box).

    [OPTIONS]
    -A, --append chain rule-specification
        Append one or more rules to the end of the selected chain.  When the source and/or destination names resolve  to  more  than
        one address, a rule will be added for each possible address combination.
    -D, --delete chain rule-specification
    -D, --delete chain rulenum
          Delete  one  or  more rules from the selected chain.  There are two versions of this command: the rule can be specified as a
          number in the chain (starting at 1 for the first rule) or a rule to match.
    -I, --insert chain [rulenum] rule-specification
          Insert one or more rules in the selected chain as the given rule number.  So, if the rule number is 1, the rule or rules are
          inserted at the head of the chain.  This is also the default if no rule number is specified.
    
    [PARAMETERS]
    -j, --jump target
          This specifies the target of the rule; i.e., what to do if the packet matches it.  The target can be  a  user-defined  chain
          (other than the one this rule is in), one of the special builtin targets which decide the fate of the packet immediately, or
          an extension (see MATCH AND TARGET EXTENSIONS below).  If this option is omitted in a rule (and -g is not used), then match‐
          ing the rule will have no effect on the packet's fate, but the counters on the rule will be incremented.
    
    [!] -p, --protocol protocol
          The  protocol  of the rule or of the packet to check.  The specified protocol can be one of tcp, udp, udplite, icmp, icmpv6,
          esp, ah, sctp, mh or the special keyword "all", or it can be a numeric value, representing one of these protocols or a  dif‐
          ferent one.  A protocol name from /etc/protocols is also allowed.  A "!" argument before the protocol inverts the test.  The
          number  zero  is equivalent to all. "all" will match with all protocols and is taken as default when this option is omitted.
          Note that, in ip6tables, IPv6 extension headers except esp are not allowed.  esp and ipv6-nonext can  be  used  with  Kernel
          version  2.6.11 or later.  The number zero is equivalent to all, which means that you cannot test the protocol field for the
          value 0 directly. To match on a HBH header, even if it were the last, you cannot use -p 0, but always need -m hbh.
    
    [!] -s, --source address[/mask][,...]
          Source specification. Address can be either a network name, a hostname, a network IP address (with /mask), or a plain IP ad‐
          dress. Hostnames will be resolved once only, before the rule is submitted to the kernel.  Please note  that  specifying  any
          name  to be resolved with a remote query such as DNS is a really bad idea.  The mask can be either an ipv4 network mask (for
          iptables) or a plain number, specifying the number of 1's at the left side of the network mask.  Thus, an iptables  mask  of
          24  is  equivalent  to 255.255.255.0.  A "!" argument before the address specification inverts the sense of the address. The
          flag --src is an alias for this option.  Multiple addresses can be specified, but this will expand to multiple  rules  (when
          adding with -A), or will cause multiple rules to be deleted (with -D).
    [!] -i, --in-interface name
          Name  of  an interface via which a packet was received (only for packets entering the INPUT, FORWARD and PREROUTING chains).
          When the "!" argument is used before the interface name, the sense is inverted.  If the interface name ends in a  "+",  then
          any interface which begins with this name will match.  If this option is omitted, any interface name will match.
    [!] -o, --out-interface name
          Name  of  an  interface  via  which  a  packet is going to be sent (for packets entering the FORWARD, OUTPUT and POSTROUTING
          chains).  When the "!" argument is used before the interface name, the sense is inverted.  If the interface name ends  in  a
          "+", then any interface which begins with this name will match.  If this option is omitted, any interface name will match.
    -m, --match match
          Specifies a match to use, that is, an extension module that tests for a specific property. The set of matches  make  up  the
          condition  under which a target is invoked. Matches are evaluated first to last as specified on the command line and work in
          short-circuit fashion, i.e. if one extension yields false, evaluation will stop.
    
    
