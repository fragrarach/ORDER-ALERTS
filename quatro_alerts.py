from sigm import add_sql_files
from listen import listen


def main():
    add_sql_files()
    listen()


if __name__ == "__main__":
    main()
