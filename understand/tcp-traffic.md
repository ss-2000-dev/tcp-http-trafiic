# TCP-HTTP 通信の理解を深めるためのドキュメント

## TCP リクエスト

```python
# with socket.socket.connect((HOST, PORT), timeout=5) as s:
with socket.create_connection((HOST, PORT), timeout=5) as s: # ①
    s.sendall(b64_bytes)
    s.shutdown(socket.SHUT_WR)  # 書き込み終わりを明示（必要）

# ①は以下の2行をまとめたもの
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.connect((HOST, PORT))
```

#### `socket.create_connection((HOST, PORT), timeout=5)`：TCP 接続を開始

- これは socket.socket() と connect() をまとめた 高レベルな便利関数
- 返ってくる s は 接続済みのソケットオブジェクト

#### `s.sendall(b64_bytes)`：TCP 接続上に バイナリデータを送信

- `.sendall()` は `.send()` と違い、全データを送信し終えるまでブロッキングする（＝確実に全部送る）関数
- TCP は一度にすべて送れるとは限りません（バッファ容量やネットワーク状況により分割される）。`.sendall()` は内部で `.send()` を繰り返し呼び、全バイトが送信されるまで待機する

### s.shutdown(socket.SHUT_WR)：送信終了の明示的なシグナルをサーバに送る

TCP には「半閉じ（half-close）」という概念がある：

- SHUT_WR … 書き込み側（送信）を閉じる。もうデータを送れない。
- SHUT_RD … 読み込み側（受信）を閉じる。もうデータを受け取らない。
  これをしないとサーバ側の recv() は「相手が送信を閉じた」と認識できず、永遠に待ち続けることがある

## TCP サーバを起動し、複数クライアントからの接続を並行処理できるようにする処理

```python
def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    s.setblocking(False)  # 非ブロッキングモード
    print(f"TCPゲートウェイサーバー起動中... {HOST}:{PORT}")
    print("Ctrl+C で停止\n")

    try:
        while True:
            # selectで0.5秒ごとに割り込み可能なaccept待ち
            readable, _, _ = select.select([s], [], [], 0.5)
            if s in readable:
                conn, addr = s.accept()
                threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
```

#### `s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)`：ソケットを作成

- AF_INET → IPv4 アドレスを使う
- SOCK_STREAM → TCP 通信（ストリーム型）を使う

#### `s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)`

- サーバーを再起動したときに TIME_WAIT 状態（ポートが一時的に使えない状態）を回避するための設定。
- SO_REUSEADDR を 1 に設定すると、直前まで使っていたポートをすぐ再利用可能にする
- TCP では切断後も数十秒間ポートが残る（TIME_WAIT 状態）
- 開発中などで何度も再起動する際に「Address already in use」エラーを防げる

#### `s.bind((HOST, PORT))`：サーバーを特定の IP アドレスとポートに紐づける

#### `s.listen()`：クライアントからの接続を待ち受け状態にする

- TCP では「3-Way Handshake」を経て接続が確立される
- この状態になると、他のプロセスから connect() が呼ばれるのを待つようになる

#### `s.setblocking(False)`：ソケットを「非ブロッキングモード」にする

#### `select.select([s], [], [], 0.5)`：どのソケットにイベントが発生したか？」を監視

- 第一引数 [s] → 「読み込み可能（接続が来た）」イベントを監視
- 0.5 秒ごとにチェック
- この行により接続がない間も CPU を使いすぎずに待機、Ctrl+C などの割り込みにも即座に反応可能

#### `conn, addr = s.accept()`：クライアントからの接続要求を受け入れ、個別の通信チャネルを作成

- conn → クライアントと通信するための新しいソケットオブジェクト。
- addr → 接続元（IP アドレス, ポート番号）のタプル。

#### `threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()`

- クライアントごとに別スレッドを作り、handle_client()で処理
- daemon=True により、メインスレッド終了時に自動で子スレッドも終了します。
- この行により複数のクライアントが同時に接続しても、各クライアントを並行（同時）に処理できる

```python
conn, addr = s.accept()
# ===== conn, addr の中身を確認 =====
print("=== accept() の戻り値 ===")
print(f"type(conn): {type(conn)}")     # <class 'socket.socket'>
print(f"type(addr): {type(addr)}")     # <class 'tuple'>

print("\n=== addr の詳細 ===")
print(f"接続元IPアドレス: {addr[0]}")   # ex.127.0.0.1
print(f"接続元ポート番号: {addr[1]}")   # ex.62004

print("\n=== conn の属性 ===")
# Python の socket モジュールが定数を数値で内部表現している
print(f"ファミリ: {conn.family}") # 2 → socket.AF_INET：IPv4を使うソケット
print(f"タイプ: {conn.type}")     # 1 → socket.SOCK_STREAM：TCP通信（コネクション型）
print(f"ローカル側のアドレス: {conn.getsockname()}") # ex.('127.0.0.1', 5000)
print(f"リモート側のアドレス: {conn.getpeername()}") # ex.('127.0.0.1', 62004)
```

##### 参考

- https://docs.python.org/3.12/library/socketserver.html
- https://docs.python.org/3.12/library/socket.html
- https://github.com/python/cpython/blob/3.12/Lib/socket.py

## ソケット通信の受信ループ

```python
def handle_client(conn, addr):
    conn.setblocking(True)
    data = b''
    try:
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            """
            Pythonの bytes はイミュータブル（変更不可）
            現状だとループごとに新しい bytes オブジェクトを生成している
            パフォーマンスのためにリストなどを使って後で b''.join() するほうがよい
            """
            data += chunk # Bad Code かも
```

#### `conn.setblocking(True)`：ブロッキングモードを有効にする

- ブロッキングとは、「データが来るまで recv() が待ち続ける」こと。
- Python のソケットはデフォルトで ブロッキングモード（明示的にしている）
- 非ブロッキングモードにした場合、データがまだ届いていないとき`recv()`がすぐに `BlockingIOError`を投げるようになる

#### `data = b''`：受信したデータを蓄積していくためのバッファ

- b'' としているのは、ソケット通信で扱うデータが バイナリ であるため

#### `chunk = conn.recv(4096)`：クライアントから送られてきたデータをト受信

- 4096 は「一度に読み取る最大バイト数」で、ネットワークバッファサイズの目安
- conn.recv()の戻り値は bytes オブジェクト
