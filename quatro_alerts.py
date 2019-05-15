import quatro
import config
import tasks


def main():
    alert_config = config.Config()
    quatro.add_sql_files(alert_config)
    quatro.listen(alert_config, tasks.listen_task)


if __name__ == "__main__":
    main()
