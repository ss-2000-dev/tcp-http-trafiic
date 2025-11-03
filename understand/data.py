import base64

#############################
# TCP Client
#############################
original = "hello from tcp client!"
print(f"original: {original}")
print(type(original))  # type(original): <class 'str'>
print() 


original_bytes = original.encode('utf-8')   # UTF-8ルールで文字列 → バイト列に変換
print(f"original_bytes: {original_bytes}")  # b'hello from tcp client!'
print(type(original_bytes))                 # <class 'bytes'>
print() 


# 各バイトの数値を確認　1バイトずつ整数で表示　各数字はそれぞれの文字の ASCIIコード（UTF-8の数値）
print(list(original_bytes))
# [104, 101, 108, 108, 111, 32, 102, 114, 111, 109, 32, 116, 99, 112, 32, 99, 108, 105, 101, 110, 116, 33]
print()


# 16進数で表示（バイナリらしく見せる）
print(original_bytes.hex())
# 68656c6c6f2066726f6d2074637020636c69656e7421
print(' '.join(f'{b:02x}' for b in original_bytes))
# 68 65 6c 6c 6f 20 66 72 6f 6d 20 74 63 70 20 63 6c 69 65 6e 74 21
print()


# Base64 エンコード → これは ASCII テキストだが bytes として送る
b64_bytes = base64.b64encode(original_bytes) # 入力としてバイト列を受け取り安全な文字列として返す
print(b64_bytes) #  b'aGVsbG8gZnJvbSB0Y3AgY2xpZW50IQ=='
print(type(original_bytes)) # <class 'bytes'>

print(' '.join(f'{b:02x}' for b in b64_bytes))
# 61 47 56 73 62 47 38 67 5a 6e 4a 76 62 53 42 30 59 33 41 67 59 32 78 70 5a 57 35 30 49 51 3d 3d