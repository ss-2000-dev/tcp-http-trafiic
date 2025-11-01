import socket
import threading
import requests
import select
import sys
import base64


HOST = '0.0.0.0'
PORT = 5000
HTTP_SERVER_URL = 'http://127.0.0.1:3000/upload'  # Node.js側のエンドポイント


def handle_client(conn, addr): 
    """クライアントごとの接続処理""" 
    print(f"📡 接続: {addr}") 
    data = b'' 
    try: 
        while True: 
            chunk = conn.recv(4096) 
            if not chunk: 
                break 
            data += chunk 
    except ConnectionResetError: 
        print(f"⚠️ クライアント {addr} が切断されました。") 
    # finally: 
    #     # conn.close() 

    if not data: 
        print("⚠️ 受信データなし")
        return 
    
    print(f"📥 tcp-gateway が受け取った raw bytes: {data!r}") 
    
    # data は Base64 の ASCII bytes で来る想定 → デコードして中身確認 
    try: 
        decoded = base64.b64decode(data) 
        print(f"🔍 デコード結果(utf-8): {decoded.decode('utf-8')}") 
    except Exception as e: 
        print(f"❌ Base64 デコード失敗: {e}") 
        return 
    
    # 次に送る別の文字列を準備して Base64 エンコード 
    next_msg = "Hello from Python TCP gateway server!" 
    next_b64 = base64.b64encode(next_msg.encode('utf-8')) # bytes 
    print(f"➡️ 次サーバへ送る Base64 (bytes): {next_b64!r}") 
    
    # HTTPでNode.jsサーバーに転送 
    print(f"📦 受信データサイズ: {len(next_b64)} bytes") 
    try: 
        headers = {'Content-Type': 'application/octet-stream'} 
        response = requests.post(HTTP_SERVER_URL, headers=headers, data=next_b64, timeout=5) 
        print(f"➡️ Node.jsサーバーへ転送完了 (status: {response.status_code})") 
        # print(f"📥 Node.jsからのレスポンス: {base64.b64decode(response.content).decode("utf-8")}\n") 
        print(f"📥 Node.jsからのレスポンス: {response.content}\n") 
    except Exception as e: 
        print(f"❌ Node.jsサーバーへの転送失敗: {e}\n")


def start_server():
    """TCPサーバーの起動"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    s.setblocking(False)  # 非ブロッキングモード
    print(f"🚀 TCPゲートウェイサーバー起動中... {HOST}:{PORT}")
    print("🧩 Ctrl+C で停止")

    try:
        while True:
            # selectで0.5秒ごとに割り込み可能なaccept待ち
            readable, _, _ = select.select([s], [], [], 0.5)
            if s in readable:
                conn, addr = s.accept()
                threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\n🛑 Ctrl + C によりサーバーを停止します。")
    finally:
        s.close()
        sys.exit(0)


if __name__ == "__main__":
    start_server()
