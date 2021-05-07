apt install -y cron
./crontab /etc/cron.d/domain-cron
./clean_old_models.py /etc/cron.d/clean_old_models.py
chmod 0644 /etc/cron.d/domain-cron
touch /var/log/cron.log
cron