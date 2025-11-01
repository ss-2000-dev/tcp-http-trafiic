import socket
import base64
import select
import sys

HOST = '0.0.0.0'
PORT = 6000


def handle_client(conn, addr):
    """クライアントからの接続を処理"""
    print(f"📡 接続: {addr}")
    try:
        conn.setblocking(True)
        data = conn.recv(4096)
        if not data:
            print("⚠️ データが空です。")
            return

        # 受信データをBase64デコードして確認
        decoded = base64.b64decode(data).decode('utf-8')
        print(f"📥 受信データ（デコード後）: {decoded}")

        response_text = f"✅ Targetからの応答: 受信内容='{decoded}'"
        encoded_response = base64.b64encode(response_text.encode('utf-8'))
        conn.sendall(encoded_response)
        print(f"📤 応答送信（エンコード後）: {encoded_response}")

    except Exception as e:
        print(f"❌ エラー: {e}")
    
    finally:
        conn.close()
        print(f"🔌 接続終了: {addr}\n")


def start_server():
    """目的のTCPサーバ起動"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        server_socket.setblocking(False)

        print(f"🚀 目的のTCPサーバ起動中... {HOST}:{PORT}")
        try:
            while True:
                # selectで接続を待機
                ready_to_read, _, _ = select.select([server_socket], [], [], 1)
                for sock in ready_to_read:
                    conn, addr = sock.accept()
                    handle_client(conn, addr)
        except KeyboardInterrupt:
            print("\n🛑 Ctrl + C によりサーバーを停止します。")
        except Exception as e:
            print(f"❌ サーバーエラー: {e}")
        finally:
            server_socket.close()
            print("🧹 ソケットをクリーンアップしました。")


if __name__ == "__main__":
    start_server()