import os
import logging

class CMDInterface:
    def __init__(self,appPath,options) -> None:
        
        self.options = options
        self.apppath = appPath
        self.logger = logging.getLogger('TRANSIT')
        self.verbose = False

    def setVerbose(self,verbose):
        self.verbose = verbose
        
    def cmdGenerator(self):
        self.optList = []
        self.optList.append(self.apppath)
        for key,value in self.options.items():
            self.optList.append(key)
            if value:
                self.optList.append(str(value))
        self.cmd = ' '.join(self.optList)
    def run(self):
        self.cmdGenerator()
        if self.verbose:
            self.logger.info(self.cmd)
        if self.verbose:
            result = os.system(self.cmd)
        else:
            result = os.system(self.cmd + ' > cmd_interface_output.txt')
        return result