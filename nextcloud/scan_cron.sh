#!/bin/sh
su -s /bin/sh -c '/usr/local/bin/php /var/www/html/occ files:scan cleanup' www-data
su -s /bin/sh -c '/usr/local/bin/php /var/www/html/occ files:scan --all' www-data