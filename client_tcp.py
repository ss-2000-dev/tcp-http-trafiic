import socket
import base64


HOST = '127.0.0.1'  # TCPサーバのアドレス
PORT = 5000         # TCPサーバのポート


def main():
    original = "hello from tcp client!"
    print(f"original: {original}")
    print(f"type(original): {type(original)}\n")

    original_bytes = original.encode('utf-8')
    print(f"original_bytes: {original_bytes}")
    print(f"type(original_bytes): {type(original_bytes)}\n")

     # Base64 エンコード → これは ASCII テキストだが bytes として送る
    b64_bytes = base64.b64encode(original_bytes)
    print(f"b64_bytes: {b64_bytes}")
    print(f"type(original_bytes): {type(original_bytes)}\n")

    print(f"送信前（元文字列）: {original}")
    print(f"送信する Base64 (bytes): {b64_bytes!r}\n")

    with socket.create_connection((HOST, PORT), timeout=5) as s:
        s.sendall(b64_bytes)
        s.shutdown(socket.SHUT_WR)  # 書き込み終わりを明示（必要）
        print("バイトデータを送信完了 → 応答待ち...")

        received = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            received += chunk

        if not received:
            print("サーバーからの応答がありません。")
            return

        decoded = base64.b64decode(received).decode("utf-8")
        print(f"サーバーからの応答（デコード後）: {decoded}\n")

    print("通信終了")


if __name__ == "__main__":
    main()
