import logging
import os

app_path_windows = r"python %SUMO_HOME%\tools\xml\xml2csv.py"
app_path_linux = r"python $SUMO_HOME/tools/xml/xml2csv.py"

output_option = '-o'

def xml2csv(input_file:str,output_file):
    logger = logging.getLogger('TRANSIT')
    if os.name == 'nt':
        app_path = app_path_windows
    else:
        app_path = app_path_linux
    logger.info('{0:-^50}'.format('Convert: '+ input_file))
    spl = input_file.rfind('/') + 1
    path = input_file[:spl]
    name = input_file[spl:]
    #output_file = path + name[:name.rfind('.')] + '.csv'
    command = ' '.join([app_path,input_file,output_option,output_file])
    rtrn = os.system(command)
    #print(r_v)
    if rtrn == 0:
        logger.info('Format convert success, file path: '+output_file)
    else:
        logger.info('Format convert failed!')
    logger.info('{0:-^50}'.format(''))

if __name__=='__main__':
    input_file = './outputs/edgeslow/detectors.out.xml'
    xml2csv(input_file,True)
    