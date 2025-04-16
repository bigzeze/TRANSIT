from TRANSIT import TRANSIT
import configparser

if __name__ == '__main__':
    app = TRANSIT()
    config = configparser.ConfigParser()
    app.set_args(**configure)
    app.check_paths()
    app.apply_simulation()