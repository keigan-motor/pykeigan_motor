## python用サンプルコード
Github

    https://github.com/keigan-motor/pykeigan_motor/tree/master/examples

## Requirements
+ python >= 3.8 (BLE を使う場合) / python >= 3.5 (USB のみ)
+ pyserial >= 3.4
+ bleak >= 0.22 (BLE。Windows 10以降 / Linux(Raspberry Pi 4/5 含む、BlueZ >= 5.55))
+ matplotlib (usb-sine-wave.py のみ)

インストール

    pip install .[ble]     # pykeigan_motor のフォルダで実行 (USB のみなら pip install .)

サンプルは examples フォルダ内のファイルから、リポジトリの pykeigan を優先して読み込みます。インストールしなくても実行できます。

Windows では `python3` の代わりに `python` を使って下さい。

## BLEサンプル

Windows / Linux(Raspberry Pi 含む) ともに、管理者権限(sudo)は不要です。

MACアドレスを引数で指定できます。省略した場合はスキャンして、見つかったモーターの一覧から番号で選択します(1台のみ見つかった場合はそのまま接続)。

    During scanning at 5.0 sec
      [0] KM-1U XXXX#54C : EF:16:B8:BB:D9:52 (RSSI -52)
      [1] KM-1U YYYY#12A : D1:5A:FA:A7:D9:5D (RSSI -70)
    Connect:[number] Rescan:[r] Quit:[q] >>

+ KM1Scan.py

    周囲の KeiganMotor をスキャンし、名前と MACアドレスを表示 (引数: スキャン秒数、省略時 5秒)
    
        $python3 KM1Scan.py
        $python3 KM1Scan.py 10

+ ble-scanner-connection.py

    スキャンして一覧から選択したモーターに接続し、LEDを黄色で点滅させる。
    
    [s] で再スキャンして別のモーターに接続し直せます。接続中のモーターはスキャンに出てこない(アドバタイズを停止する)ため、スキャン前に切断します。その他のキーで終了。
    
        $python3 ble-scanner-connection.py

+ ble-simple-connection.py

    基本的な接続。LEDを黄色で点滅させ、5rpmで正転。キー入力で停止・切断。
    
        $python3 ble-simple-connection.py
        $python3 ble-simple-connection.py xx:xx:xx:xx:xx:xx

+ ble-rotate-the-motor.py

    モーターを5rpmで 正転(10秒) -> 逆転(10秒) -> 停止(トルクあり, 10秒) -> 停止(トルク無し)
    
        $python3 ble-rotate-the-motor.py
        $python3 ble-rotate-the-motor.py xx:xx:xx:xx:xx:xx
             
+ ble-get-motor-Informations.py

    モーターのステータス・回転情報(位置/速度/トルク)・IMU情報を 0.5秒ごとに表示。キー入力で終了。
    
        $python3 ble-get-motor-Informations.py
        $python3 ble-get-motor-Informations.py xx:xx:xx:xx:xx:xx

+ ble_select.py

    BLE サンプル共通の「スキャンして選択」処理 (直接は実行しません)。
    
        from ble_select import select_motor
        address = select_motor()          # 選択された MACアドレス (中止時は None)

### プログラムからの使い方

    from pykeigan import blecontroller

    print(blecontroller.scan(5.0))        # [{'name': ..., 'address': ..., 'rssi': ...}, ...]
    dev = blecontroller.BLEController("xx:xx:xx:xx:xx:xx")
    dev.on_motor_measurement_value_cb = lambda m: print(m)   # USB と同じコールバックが使える
    dev.enable_continual_motor_measurement()
    dev.enable_action()
    dev.set_speed(1.0)
    dev.run_forward()

+ 回転情報・IMU情報・レジスタ値は BLE の notify で受信します。`on_motor_measurement_value_cb` / `on_motor_imu_measurement_cb` / `on_motor_log_cb` / `on_motor_event_cb` を USBController と同様に使えます。コールバックはバックグラウンドのスレッドから呼ばれます。
+ `read_motor_measurement()` / `read_imu_measurement()` は最新の受信値を返します(受信が無い場合は直接読み出し)。

### Bluetoothでモーターが検出されない場合

+ スマートフォンのアプリ(KMQuick など)や他の PC が接続していると、モーターはアドバタイズを止めるため検出できません。アプリを終了して下さい。
+ USB で接続した後は BLE が無効になっていることがあります。KMQuick などで BLE を有効にするか、モーターを再起動して下さい。
+ 切断直後は数秒間検出されないことがあります。
+ Raspberry Pi では bluetooth サービスが動作していることを確認して下さい。

        sudo systemctl enable --now bluetooth

+ それでも検出されない場合は、モーターの"インターフェイスのリセット"を実行して下さい。

        https://document.keigan-motor.com/basic/reset


## USBサンプル

引数でデバイスファイル(ポート)を指定します (省略時 /dev/ttyUSB0)。

+ Linux: `/dev/ttyUSB0` または `/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_DM00XXXX-if00-port0`
+ Windows: `COM3` など (デバイスマネージャーの「ポート (COM と LPT)」で確認)

        $python3 usb-simple-connection.py /dev/ttyUSB0
        > python usb-simple-connection.py COM3

+ usb-simple-connection.py

    基本的な接続。LEDを黄色で点滅させ、5rpmで正転。キー入力で終了。
    
        $python3 usb-simple-connection.py [PORT]
        
+ usb-actuator.py

    モーターの往復運動。20rpm で 0° と 720°(2回転) の絶対位置を往復。キー入力で終了。
    
        $python3 usb-actuator.py [PORT]
    
+ usb-button_trigger.py

    KeiganMotor 本体のボタンイベント取得。ボタンを押すと番号を表示。
    
    ※ ポートは引数ではなく、ファイル内の `port1` を書き換えて下さい。
    
        $python3 usb-button_trigger.py

+ usb-get-motor-Informations.py

    モーターの回転情報(位置/速度/トルク)と IMU情報を表示しながら 1.0rad/sec で正転。キー入力で終了。
    
    モーター時刻付きの回転情報を有効にします(モーターFW ver 2.62以降)。
    
        $python3 usb-get-motor-Informations.py [PORT]

+ usb-get-motor-Info-time.py

    usb-get-motor-Informations.py からモーター時刻送信の設定を除いたもの (FW ver 2.62 未満でも使用可)
    
        $python3 usb-get-motor-Info-time.py [PORT]
        
+ usb-position-control.py

    モーターの相対・絶対移動
    
        $python3 usb-position-control.py [PORT]

+ usb-offset-position-control.py

    モーターの原点を書き換えず、プログラム側のオフセット(OFFSET_DEG)で機械の0°を決めて絶対位置移動

    --measure を付けると現在位置を表示するだけで終了します(モーターは動きません)。表示された値を OFFSET_DEG に設定してから実行して下さい。
    
        $python3 usb-offset-position-control.py [PORT] --measure
        $python3 usb-offset-position-control.py [PORT]

+ usb-move_wait_queue.py

    位置到達を待ってから次の動作を行う (move_to_pos_wait)。100rpm で 0° -> 90° -> 0° -> -90° -> 0° と移動。Ctrl-C で終了。
    
        $python3 usb-move_wait_queue.py [PORT]
        
+ usb-rotate-the-motor.py

    モーターを5rpmで 正転(10秒) -> 逆転(10秒) -> 停止(トルクあり) -> 停止(トルク無し)
    
        $python3 usb-rotate-the-motor.py [PORT]

+ usb-sine-wave.py

    正弦波の位置指令で往復させ、結果をグラフ表示 (matplotlib が必要。Linux 用: signal のタイマーを使用)
    
        $python3 usb-sine-wave.py [PORT]
   
+ usb-teaching-control.py

    ティーチング記録・再生。[r] 記録 / [p] 再生 / [w] テスト動作の書き込み / [m] 記録した動作の読み出し / その他のキーで終了
    
        $python3 usb-teaching-control.py [PORT]
        
+ usb-torque-control.py

    トルク制御。モーターを手で回して行くとトルクが加算される。[s] 開始 / [r] リセット / その他のキーで終了
    
        $python3 usb-torque-control.py [PORT]


## Windows 用 USB サンプル (windows_examples)

Windows 専用 (キー入力に msvcrt を使用) です。多くのサンプルは起動時に COM ポートの一覧を表示するので、番号を入力して選択します。

    > cd examples\windows_examples
    > python run.py

+ run.py

    [r] 5rpm で正転 / [s] 停止。Ctrl-C で終了。※ ポートはファイル内の `port = 'COM7'` を書き換えて下さい。

+ select_port_run.py

    COM ポートを選択して接続。[r] 50rpm で正転 / [s] 停止 / [a] モーター再起動。Ctrl-C で終了。

+ motor_measurement.py

    COM ポートを選択し、1.0rad/sec で正転しながら回転情報と IMU情報を表示。

+ move_wait_queue.py

    位置到達を待って次の動作を行う (move_to_pos_wait)。usb-move_wait_queue.py の COM ポート選択版。

+ move_to_continious.py

    [f] 1080° へ移動 / [b] 0° へ移動。ダイレクト位置制御 (curve_type 10) と safe_run を使用。

+ pos_arrival_test.py

    0° と 1080° の往復を、位置到達通知 (KM_SUCCESS_ARRIVAL) を受けて繰り返す。

+ run_continious.py

    20rpm で連続回転。safe_run (1秒以内に次の指令が無いと停止) を使用。

+ sine_wave_move.py

    正弦波の位置指令で往復させる。
    ※ signal.setitimer / SIGALRM を使用しているため、現状 Windows では動作しません (Linux では動作)。

+ pid_settings.py

    [r] PID値の読み出し / [n] デバイス名の読み出し / [s] 全設定の保存 / [d] PIDを初期値に戻す / [b] 再起動

+ reset_all.py

    [r] 全レジスタを初期値に戻して保存 (モーターの設定がすべて初期化されます)

+ baudrate_change.py / baudrate_run.py

    ボーレートの変更 (baudrate_change.py) と、変更後のボーレートでの動作確認 (baudrate_run.py)。
    baudrate_change.py は現在のボーレートをファイル内の `current_baud` に設定してから実行して下さい。設定はモーターに保存されます。

+ keigan_motor_initial_setting.py

    ボーレートを 1Mbps に変更し、回転情報の送信間隔を最短に設定して保存する初期設定サンプル。

+ keigan_motor_measurement_test.py

    回転情報の受信テスト。ファイル内の `measurement_method` で "callback" (コールバック) か "read" (read_motor_measurement) を選択。

+ taskset_run.py / taskset_move.py

    タスクセットの記録と実行。[r] タスクセットを記録 / [d] 実行。
    ファイル内の `port`、`index` (0〜49)、`repeat` (0 で無限) を設定してから実行して下さい。
