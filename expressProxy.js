const express = require("express");
const net = require("net");
const app = express();

const TCP_TARGET_HOST = "127.0.0.1";
const TCP_TARGET_PORT = 6000;

app.post(
  "/upload",
  express.raw({ type: "application/octet-stream", limit: "50mb" }),
  async (req, res) => {
    try {
      const b64Buffer = req.body;
      console.log("Express が受け取った raw Buffer length:", b64Buffer.length);
      console.log(`typeof(b64Buffer): ${b64Buffer}`);

      // Base64 をデコードして中身確認
      const b64String = b64Buffer.toString("ascii"); // Base64 は ASCII テキスト
      const decoded = Buffer.from(b64String, "base64").toString("utf8");
      console.log("デコード結果 (utf-8):", decoded);

      // TCP通信をPromiseで包んで「送信＋応答受信」を待つ
      const responseB64 = await new Promise((resolve, reject) => {
        const client = new net.Socket();
        let responseChunks = [];

        client.connect(TCP_TARGET_PORT, TCP_TARGET_HOST, () => {
          console.log("目的のTCPサーバへ送信");
          client.write(b64Buffer); // Base64エンコード済みのまま送る
        });

        client.on("data", (data) => {
          console.log("目的のTCPサーバから応答受信:", data.length, "bytes");
          responseChunks.push(data);
        });

        client.on("end", () => {
          const fullResponse = Buffer.concat(responseChunks);
          resolve(fullResponse); // Base64文字列のバイト列を返す
        });

        client.on("error", (err) => {
          console.error("TCPクライアントエラー:", err.message);
          reject(err);
        });
      });

      // Node.js → Python Gateway へのHTTPレスポンスとして返す
      res
        .status(200)
        .set("Content-Type", "application/octet-stream")
        .send(responseB64); // targetからの応答(Base64)をそのまま返す

      console.log("HTTPレスポンス返却完了\n");

      // TCPクライアント接続を閉じた後にレスポンスを返す
    } catch (err) {
      console.error("Express ハンドラエラー:", err);
      res.status(500).send("error");
    }
  }
);

app.listen(3000, () => {
  console.log("Expressサーバ起動: http://localhost:3000");
});
