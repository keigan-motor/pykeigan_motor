# Read me 

## Description / 説明
Program for logging motor data (external)  
モーターのログ書き出しプログラム  

### File / ファイル
1. log.py  
main function / メイン関数
2. sample.py  
sample code of how to use / 利用例のコード 

### How to Use / 使い方
1. Importing `log.py` / `log.py`をインポートする
```
import log
```
2. Creating a MotorLog / MotorLogの作成  
モータ(dev)の起動パラメータを全て設定した後に行ってください。  
  
```
motor_log = log.MotorLog(dev)
```
3. start logging / ログ開始
```
motor_log.startLogging()
```
4. to finish logging, please use the command below  
ログ終了したい場合は以下のコマンドを使用します。  
```
motor_log.stopLogging()
```
5. to pause and resume logging, please use the command below (respectively)  
ロギングを一時停止、再開するには、以下のコマンドを使用します。  
```
motor_log.pauseLogging()
motor_log.resumeLogging()
```

6. To add additional message to log file, please use the command below  
ログファイルにメッセージを追加するには、以下のコマンドを使用してください。 
```
motor_log.additionalLog('addtional message')
```

For a sample of how to use, please refer to `sample.py`  
利用例のコードは`sample.py`をご参考ください。

### Note / ノート
#### Parameter / パラメータ
> MotorLog(*motor*, *file_name(optional)*, *interval_second(optional)*, *overwriteCb(optional)*)

| parameter/パラメータ | type/タイプ      | default value / デフォルト値 | explanation/説明                                        |
|-----------------|---------------|------------------------|-------------------------------------------------------|
| motor           | USBController | -                      | motor to log / ログ書き出しのモーター                            |              
| file_name       | string        | port name              | file name of log / ログファイル名                            |
| interval        | number        | 1                      | interval between getting data (sec) / データを取得する間隔（秒）      |
| overwriteCb     | boolean       | True                   | overwrite callback to emit log / コールバックにログを書き出すように上書き |


sample / 例 : `MotorLog(dev, 'Test_Motor', 2)`

#### File name / ファイル名
`file_name.log.YYYY-mm-dd_HH-MM-SS`  
sample / 例 : `Test_Motor.log.2023-01-11_08-55-22`  

#### Log format / ログフォーマット
`Timestamp | {pos, vel, toq, unix, motor}, {enable, queue, ctrl}`  

| parameter/パラメータ | explanation/説明                       |
|-----------------|--------------------------------------|
| Timestamp       | current datetime / 現在 datetime       |
| pos             | position (3 decimal digit / 小数第3位)   |
| vel             | velocity (3 decimal digit / 小数第3位) 　 | 
| toq             | toque　(3 decimal digit / 小数第3位) 　    |
| unix            | received_unix_time                   |
| motor           | motor_time                           |
| enable          | motorEnabled                         |
| queue           | queue                                |
| ctrl            | motor_control_mode                   |

sample / 例 : 
`2023-01-12 10:39:42.046269 | {pos:41.827,vel:0.226,toq:0.038,unix:1673487582.003,motor:3541267}{enable:1,queue:0,ctrl:MOTOR_CONTROL_MODE_VELOCITY}`  

additional message will be logged with *[add]* tag.  
追加メッセージは、*[add]*タグで記録されます。  
  
sample / 例 : 
`2023-01-12 10:39:40.917516[add] | {'command_names': 96, 'error_codes': 0}`

#### callback log / コールバックのログ
| Callback/コールバック                   | tag/タグ      | format/フォーマット              | sample/例                                  |
|-----------------------------------|-------------|----------------------------|-------------------------------------------|
| on_motor_log_cb                   | log         | command_names, error_codes | `{'command_names': 96, 'error_codes': 0}` |
| on_motor_reconnection_cb          | reconnect   | reconn_err_cnt             | `4`                                       |
| on_motor_connection_error_cb      | connect err | error message              | `[Errno 5] Input/output error`            |

**warning**  
In case any of the listed callback is used in main program, ALL needed callback log has to be added manually
(please call `additionalLog(msg)` function)  
please refer to `sample.py` for a sample code

**注意**  
リストされたコールバックのいずれかがメインプログラムで使用される場合、他の必要なログもコールバックに手動で追加する必要があります。  
（`additionalLog(msg)` 関数使ってください）  
サンプルコードについては `sample.py` を参照してください。  



#### Log Rotation / ログローテーション
Log file will be automatically rotated every 4 hours.  
The last log before rotating will be saved as `file_name.log`.  
In case logging is ended properly (`stopLogging()` is called), the last file will be automatically created (`file_name.log.YYYYmmdd-HHMMSS` format).  
  
**warning**  
- if logging is not ended properly, please manually back up the last log file, otherwise it might be replaced with the next running  
- The number of backup file for each *file_name* is up to 120 files (if exceeded, the oldest file will be deleted).  
  
4時間毎に自動的にログファイルローテーション行います。  
ローテーション前の最後のログは`file_name.log`として保存されます。  
ログプログラムが適切に終了した（`stopLogging()`呼ばれた）場合は、最後のログは自動でバックアップされます（`file_name.log.YYYYmmdd-HHMMSS`フォーマット）。  
  
**注意**  
- ログプログラムが適切に終了していない場合は、最後のログファイルを手動でバックアップしてください。次のプログラム実行に以前のプログラムのログが上書きされる可能性があります。  
- 各*file_name*のログは120ファイルまで。（120ファイルを超えた場合は最古のログから削除されます）