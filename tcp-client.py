import socket
import base64


HOST = '127.0.0.1'  # TCPサーバのアドレス
PORT = 5000         # TCPサーバのポート


def main():
    original = "Hello from TCP client !"
    print(f"original: {original}")
    print(f"type(original): {type(original)}")

    original_bytes = original.encode('utf-8')
    print(f"original_bytes: {original_bytes}")
    print(f"type(original_bytes): {type(original_bytes)}")

     # Base64 エンコード → これは ASCII テキストだが bytes として送る
    b64_bytes = base64.b64encode(original_bytes)  # type: bytes
    print(f"b64_bytes: {b64_bytes}")
    print(f"type(original_bytes): {type(original_bytes)}")

    print(f"➡️ 送信前（元文字列）: {original}")
    print(f"➡️ 送信する Base64 (bytes): {b64_bytes!r}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(b64_bytes)
    print("✅ バイナリデータを送信しました。")


if __name__ == "__main__":
    main()

