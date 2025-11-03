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
    print(f"---------- 接続: {addr} ----------\n") 
    conn.setblocking(True) # なくても動作はする

    chunks = [] 
    try: 
        while True: 
            chunk = conn.recv(4096) 
            if not chunk: 
                print("クライアントが接続を閉じました\n")
                break 
            chunks.append(chunk)  # bytesをそのまま追加
            print(f"{len(chunk)} バイト受信")
    except ConnectionResetError: 
        print(f"クライアント {addr} が切断されました。") 

    # 全チャンクをまとめて1つのbytesに結合
    data = b"".join(chunks)
    print(f"受信完了: 総バイト数 {len(data)}")
    
    if not data: 
        print("受信データなし")
        return 
    
    print(f"tcp-gateway が受け取ったデータサイズ: {data!r}") 
    
    # data は Base64 の ASCII bytes で来る想定 → デコードして中身確認 
    try: 
        decoded = base64.b64decode(data) 
        print(f"デコード結果(utf-8): {decoded.decode('utf-8')}\n") 
    except Exception as e: 
        print(f"Base64 デコード失敗: {e}") 
        return 
    
    # 次に送る別の文字列を準備して Base64 エンコード 
    next_msg = decoded.decode('utf-8') + ", python tcp gateway server!" 
    print(f"次サーバへ送るメッセージ: {next_msg}") 
    next_b64 = base64.b64encode(next_msg.encode('utf-8')) # bytes 
    print(f"次サーバへ送る Base64 (bytes): {next_b64!r}\n") 
    
    # HTTPでNode.jsサーバーに転送 
    try: 
        headers = {'Content-Type': 'application/octet-stream'} 
        response = requests.post(HTTP_SERVER_URL, headers=headers, data=next_b64, timeout=5) 
        print(f"Node.jsサーバーへ転送完了 (status: {response.status_code})") 
    except Exception as e: 
        print(f"Node.jsサーバーへの転送失敗: {e}\n")
        conn.close()
        return
    
    # Node.js からの応答（Base64のbytes）を受信
    if response.content:
        try:
            # Base64デコードして中身を確認
            decoded_text = base64.b64decode(response.content).decode("utf-8")
            print(f"Node.jsからのレスポンス(デコード後): {decoded_text}")

            # メッセージに追加情報を付与
            modified_msg = decoded_text + ", python tcp gateway server!"
            print(f"クライアントへ返すメッセージ: {modified_msg}")

            # Base64に再エンコード
            modified_b64 = base64.b64encode(modified_msg.encode("utf-8"))
            print(f"クライアントへ返す Base64 (bytes): {modified_b64!r}\n")

            # TCPクライアントへ送信
            conn.sendall(modified_b64)
            conn.shutdown(socket.SHUT_WR)
            print("クライアントへ応答送信完了")
        except Exception as e:
            print(f"クライアントへの応答送信失敗: {e}")
    
    else:
        print("Node.jsから応答なし。")

    conn.close()
    print(f"\n---------- 接続終了: {addr} ----------\n")


def start_server():
    """TCPサーバーの起動"""
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
    except KeyboardInterrupt:
        print("Ctrl + C によりサーバーを停止します。")
    except Exception as e:
        print(f"サーバーエラー: {e}")
    finally:
        s.close()
        print("ソケットをクリーンアップしました。")
        sys.exit(0)


if __name__ == "__main__":
    start_server()
