from time import sleep
from datetime import datetime
import threading

import logging
import logging.handlers as handlers
import shutil
import os


class MotorLog(object):
    def __init__(self, motor, fileName='', interval=1, overwriteCb=True):
        """
        Initiate log / ログ生成
        :param motor: USBController
            motor to log
            ログ書き出しのモーター
        :param fileName: string, optional
            file name of log, default is port name of the motor (generated log file format: file_name.log.YYYY-mm-dd_HH-MM-SS)
            ログファイル名、デフォルトはモーターのポート名 (作成ログファイルフォーマット：file_name.log.YYYY-mm-dd_HH-MM-SS)
        :param interval: number, optional
            interval between getting data and writing log (sec), default is 1
            データ得る・ログ書き出し間隔（秒）、デフォルトは１
        :param overwriteCb : boolean
            overwrite motor call back (on_motor_log_cb, on_motor_reconnection_cb, on_motor_connection_error_cb) to emit log, default is True
            モーターのコールバック (on_motor_log_cb, on_motor_reconnection_cb, on_motor_connection_error_cb) にログを書き出すように上書き、デフォルトはTrue
        """
        print('\33[33m',
              "\n\nInitiate MotorLog (\'"+fileName + "\', "+motor.port + ", " + str(
                  interval) + ", "+str(overwriteCb)+")\n", '\33[0m')

        if not os.path.exists('log'):
            os.makedirs('log')

        self.dev = motor
        self.interval = interval
        self.isConnected = True
        self.isLogging = False
        self.pause = False
        self.fileName = 'log/'
        if fileName=='':
            self.fileName += motor.port.split('/')[-1]
        else:
            self.fileName += fileName

        if overwriteCb:
            motor.on_motor_log_cb = self.overwriteMotorLogCb
            motor.on_motor_reconnection_cb = self.overwriteMotorReconnectionCb
            motor.on_motor_connection_error_cb = self.overwriteMotorConnectionErrCb


        self.logger = logging.getLogger(self.fileName)
        self.logger.setLevel(logging.DEBUG)
        logHandler = handlers.TimedRotatingFileHandler(self.fileName+'.log', when='H', interval=4, backupCount=120)
        #logHandler.suffix = "%Y%m%d-%H%M%S"
        logHandler.setLevel(logging.DEBUG)
        self.logger.addHandler(logHandler)

        header = self.fileName + "-" + self.dev.port + "(" + str(self.interval) + ")"
        if overwriteCb:
            header += "cb"
        self.logger.debug(header)

    def overwriteMotorLogCb(self, msg):
        """
        Emit log when on_motor_log_cb (Internal use)
        on_motor_log_cbからログ書き出し（内側利用）
        :param msg: message from callback / コールバックからのメーセージ
        """
        #print('log {} '.format(msg))
        log = str(datetime.now()) + " <log> | " + str(msg)
        self.logger.debug(log)

    def overwriteMotorReconnectionCb(self, msg):
        """
        Emit log when on_motor_reconnection_cb (Internal use)
        on_motor_reconnection_cb（内側利用）
        :param msg: message from callback / コールバックからのメーセージ
        """
        #print('log {} '.format(msg))
        log = str(datetime.now()) + " <reconnect> | " + str(msg)
        self.logger.debug(log)

    def overwriteMotorConnectionErrCb(self, msg):
        """
        Emit log when on_motor_connection_error_cb (Internal use)
        on_motor_connection_error_cb（内側利用）
        :param msg: message from callback / コールバックからのメーセージ
        """
        #print('log {} '.format(msg))
        log = str(datetime.now()) + " <connect err> | " + str(msg)
        self.logger.debug(log)

    def startLogging(self):
        """
        Start logging / ログ開始
        """
        print('\33[33m', "\n\nStart logging (filename: "+self.fileName+", port:" + self.dev.port + ", interval:" + str(self.interval) + " s)\n", '\33[0m')
        log = str(datetime.now()) + " [START]"
        self.logger.debug(log)

        self.isLogging = True
        self.pause = False
        t = threading.Thread(target=self.readMotor)
        t.start()

    def pauseLogging(self):
        """
        Pause logging / ログ一時停止
        Not available if logging is not started
        ログ開始していない状態は利用不可
        """
        print('\33[33m', "Pause logging (filename: "+self.fileName+", port:" + self.dev.port + ", interval:" + str(self.interval) + " s)\n", '\33[0m')
        log = str(datetime.now()) + " [PAUSE]"
        self.logger.debug(log)
        if not self.isLogging:
            print('\33[33m', "[Error] logging is not started", '\33[0m')
        else:
            self.pause = True

    def resumeLogging(self):
        """
        Resume logging / ログ再開
        Not available if logging is not started
        ログ開始していない状態は利用不可
        """
        print('\33[33m', "Resume logging (filename: "+self.fileName+", port:" + self.dev.port + ", interval:" + str(self.interval) + " s)\n", '\33[0m')
        log = str(datetime.now()) + " [RESUME]"
        self.logger.debug(log)
        if not self.isLogging:
            print('\33[33m', "[Error] logging is not started", '\33[0m')
            #try:
            #    print('\33[33m', "\tTry restart logging...", '\33[0m')
            #    self.startLogging()
            #except:
            #    print('\33[33m', "\t...cannot restart logging", '\33[0m')
        else:
            self.pause = False

    def stopLogging(self):
        """
        Stop logging and backup latest log / ログ終了、最後のログバックアップ
        """
        print('\33[33m', "\n\nStop logging (filename: "+self.fileName+", port:" + self.dev.port + ", interval:" + str(self.interval) + " s)\n", '\33[0m')
        log = str(datetime.now()) + " [STOP]"
        self.logger.debug(log)
        self.isLogging = False
        sleep(2)
        self.backupLastLog()

    def backupLastLog(self):
        """
        Backup latest log / 最後のログバックアップ
        """
        #latestLog = self.fileName + '.log.' + str(datetime.now().strftime('%Y%m%d-%H%M%S'))
        latestLog = self.fileName + '.log.' + str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
        print('\33[33m', "back up latest log: " + latestLog, '\33[0m')
        shutil.copyfile(self.fileName + '.log', latestLog)

    def readMotor(self):
        """
        Read motor data and write data to log / モーターデータ取得・ログに書き出し
        log format - Timestamp | {pos, vel, toq, unix, motor}, {enable, queue, ctrl}
        """
        if not self.isLogging:
            print('\33[33m', "[Error] logging is not started (filename: "+self.fileName+", port:" + self.dev.port + ", interval:" + str(self.interval) + " s)\n", '\33[0m')

        while self.isLogging:
            if not self.pause:
                try:
                    log = ''

                    if not self.dev.is_connected():
                        log += str(datetime.now()) + " | "
                        log += "Disconnected\n"
                        self.isConnected = False
                    elif not self.isConnected:
                        log += str(datetime.now()) + " | "
                        log += "Connected\n"
                        self.isConnected = True

                    try:
                        log += str(datetime.now()) + " | "

                        measurement = self.dev.read_motor_measurement()
                        pos = str(round(measurement['position'], 3))
                        vel = str(round(measurement['velocity'], 3))
                        toq = str(round(measurement['torque'], 3))
                        unix = str(round(measurement['received_unix_time'], 3))


                        log +="{pos:"+pos+",vel:"+vel+",toq:"+toq+",unix:"+unix
                        try:
                            motor = str(measurement['motor_time'])
                            log += ",motor:" + motor
                        except:
                            pass

                        log +="}"

                        status = self.dev.read_status()
                        motor_enable = str(status['motorEnabled'])
                        queue = str(status['queue'])
                        ctrl = str(status['motor_control_mode'])

                        log += "{enable:" + motor_enable + ",queue:" + queue + ",ctrl:" + ctrl + "}"

                        #status {'isCheckSumEnabled': 1, 'iMUMeasurement': 0, 'motorMeasurement': 1, 'queue': 0, 'motorEnabled': 0, 'flash_memory_state': 'FLASH_STATE_READY', 'motor_control_mode': 'MOTOR_CONTROL_MODE_NONE'}
                        #print(self.fileName+'\tstatus {} '.format(self.dev.read_status()))

                        #measurement {'position': 12.35468578338623, 'velocity': 0.0037638440262526274, 'torque': 0.008983751758933067, 'received_unix_time': 1673331919.671698, 'motor_time': 2465588}
                        #print(self.fileName+'\tmeasurement {} '.format(self.dev.read_motor_measurement()))



                    except Exception as e:
                        #print('\33[31m', e, '\33[0m')
                        pass

                    #print(log)
                    self.logger.debug(log)

                    sleep(self.interval)

                except:
                    print('\33[33m', "\n\nLogging end by interrupt (filename: "+self.fileName+", port:" + self.dev.port + ", interval:" + str(self.interval) + " s)\n", '\33[0m')
                    self.backupLastLog()
                    return

        print('\33[33m', "\n\nLogging end (filename: "+self.fileName+", port:" + self.dev.port + ", interval:" + str(self.interval) + " s)\n", '\33[0m')

    def additionalLog(self, msg):
        """
        Insert additional message to log / ログに追加メーセージ書き出し
        :param msg: string
            message to log
        """
        log = str(datetime.now()) + " [add] | " + str(msg)
        self.logger.debug(log)
