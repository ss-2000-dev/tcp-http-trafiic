const express = require("express");
const net = require("net");
const app = express();

const TCP_TARGET_HOST = "127.0.0.1";
const TCP_TARGET_PORT = 6000;

app.post(
  "/upload",
  express.raw({ type: "application/octet-stream", limit: "50mb" }),
  async (req, res) => {
    console.log("---------- リクエスト受信 ----------\n");
    try {
      const b64Buffer = req.body;
      console.log("Express が受け取った raw Buffer length:", b64Buffer.length);
      console.log(`type: ${typeof b64Buffer}`);
      console.log("b64Buffer: b64Buffer\n");

      // Base64 をデコードして中身確認
      const b64String = b64Buffer.toString("ascii"); // Base64 は ASCII テキスト
      const decoded = Buffer.from(b64String, "base64").toString("utf8");
      console.log(`デコード結果 (utf-8): ${decoded}\n`);

      const message = decoded + ", node proxy server!";
      console.log(`次サーバへ送るメッセージ: ${message}`);
      const messageB64 = Buffer.from(message, "utf8").toString("base64");
      //   const messageB64 = Buffer.from(message, "utf8"); これだとダメ
      console.log(`次サーバへ送る Base64 (bytes): ${messageB64}\n`);

      // TCP通信をPromiseで包んで「送信＋応答受信」を待つ
      const responseB64 = await new Promise((resolve, reject) => {
        const client = new net.Socket();
        let responseChunks = [];

        client.connect(TCP_TARGET_PORT, TCP_TARGET_HOST, () => {
          client.write(messageB64); // Base64エンコード済みのまま送る
          console.log("目的のTCPサーバへ送信完了\n");
        });

        client.on("data", (data) => {
          console.log("目的のTCPサーバから応答受信:", data.length, "bytes");
          responseChunks.push(data);
        });

        client.on("end", () => {
          const fullResponse = Buffer.concat(responseChunks);

          const decodedResponse = Buffer.from(
            fullResponse.toString("ascii"),
            "base64"
          ).toString("utf8");
          console.log("🔍 デコード結果:", decodedResponse);

          const modifiedMessage = decodedResponse + ", node proxy server!";
          console.log("🧩 追記後のメッセージ:", modifiedMessage);

          // 再度 Base64 エンコード
          const modifiedB64 = Buffer.from(modifiedMessage, "utf8").toString(
            "base64"
          );
          console.log("📤 再エンコード(Base64):", modifiedB64);

          resolve(Buffer.from(modifiedB64, "ascii"));
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

      console.log("\n---------- レスポンス送信完了 ----------\n");

      // TCPクライアント接続を閉じた後にレスポンスを返す
    } catch (err) {
      console.error("Express ハンドラエラー:", err);
      res.status(500).send("error");
    }
  }
);

app.listen(3000, () => {
  console.log("Expressサーバ起動: http://localhost:3000\n");
});
