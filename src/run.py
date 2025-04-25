from TRANSIT import TRANSIT
import configparser
import os

path = os.path.dirname(os.path.abspath(__file__)) + '/'

if __name__ == '__main__':
    app = TRANSIT()
    # 修改: 设置 optionxform 为 str，以区分大小写
    parser = configparser.ConfigParser()
    parser.optionxform = str
    scenario = 'theoretical_streets'
    '''
    'theoretical_streets'
    'real_world_streets'
    'real_world_expressways'
    'parallel'
    '''
    anomaly = 'speed_limit'
    '''
    'speed_limit'
    'traffic_light_failure'
    'abrupt_flow'
    '''
    config_path = path + '../' + 'configs/' + scenario + '/' + anomaly + '.ini'
    # 读取配置文件
    parser.read(config_path, encoding='utf-8')
    configure = dict(parser['Configuration'])

    # 修改: 将配置中的值转换为 int 或 float 类型
    for key, value in configure.items():
        try:
            configure[key] = int(value)
        except ValueError:
            try:
                configure[key] = float(value)
            except ValueError:
                pass

    app.set_args(**configure)
    app.check_paths()
    app.apply_simulation()