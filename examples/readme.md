## python用サンプルコード
Github

    https://github.com/keigan-motor/pykeigan_motor/examples

## Requirements
+ python >= 3.5 (recommended) or 2.6
+ pyserial >= 3.4
+ bleak >= 0.22 (BLE, Windows / Linux(Raspberry Pi 4/5 含む))

## BLEサンプル

+ KM1Scan.py 
    
    Bluetooth接続で使用するKeiganMotorのモーターのMACアドレスを検出するのに使用
    
    管理者権限(sudo)は不要です
    
        $python3 KM1Scan.py

+ ble-scanner-connection.py

    管理者権限(sudo)は不要です
    
        $python3 ble-scanner-connection.py

+ ble-simple-connection.py

    実行前にモーターのMACアドレスを設定する必要があります。
    
        $python3 ble-simple-connection.py

+ ble-rotate-the-motor.py

    実行前にモーターのMACアドレスを設定する必要があります。
    
        $python3 ble-rotate-the-motor.py
             
+ ble-get-motor-Informations.py

    モーターの回転情報の取得
    
    実行前にモーターのMACアドレスを設定する必要があります。
    
        $python3 ble-get-motor-Informations.py


MACアドレスはKM1Scan.pyを使用するか"nRF Connect"を使用して調べて下さい。 

    nRF Connect
    https://play.google.com/store/apps/details?id=no.nordicsemi.android.mcp
            
Bluetoothでモーターが検出されない場合は、モーターの"インターフェイスのリセット"を実行して下さい。

    https://document.keigan-motor.com/basic/reset


## USBサンプル

実行前にデバイスファイルを指定する必要があります ex'/dev/ttyUSB0'

+ usb-simple-connection.py

    基本的な接続
    
        $python3 usb-simple-connection.py
        
+ usb-actuator.py

    モーターの往復運動
    
        $python3 usb-actuator.py
    
+ usb-button_trigger.py

    KeiganMotor 本体のボタンイベント取得
    
        $python3 usb-button_trigger.py

+ usb-get-motor-Informations.py

    モーターの回転情報の取得
    
        $python3 usb-get-motor-Informations.py
        
+ usb-position-control.py

    モーターの相対・絶対移動
    
        $python3 usb-position-control.py

+ usb-offset-position-control.py

    モーターの原点を書き換えず、プログラム側のオフセット(OFFSET_DEG)で機械の0°を決めて絶対位置移動

    --measure を付けると現在位置を表示するだけで終了します(モーターは動きません)。表示された値を OFFSET_DEG に設定してから実行して下さい。
    
        $python3 usb-offset-position-control.py /dev/ttyUSB0 --measure
        $python3 usb-offset-position-control.py /dev/ttyUSB0
        
+ usb-rotate-the-motor.py

    モーターを5rpmで 正転(10秒) -> 逆転(10秒) -> 停止(トルクあり) -> 停止(トルク無し)
    
        $python3 usb-rotate-the-motor.py
        
   
+ usb-teaching-control.py

    ティーチング記録・再生
    
        $python3 usb-teaching-control.py
        
+ usb-torque-control.py

    トルク制御。モーターを手で回して行くとトルクが加算される。
    
        $python3 usb-torque-control.py
