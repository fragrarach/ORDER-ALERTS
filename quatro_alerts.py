from quatro import init_app_log_dir, log, add_sql_files, listen
import config
import tasks


def main():
    init_app_log_dir()
    log(f'Starting {__file__}')
    alert_config = config.Config()
    add_sql_files(alert_config)
    listen(alert_config, tasks.listen_task)


if __name__ == "__main__":
    main()
