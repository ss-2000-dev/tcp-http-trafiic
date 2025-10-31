const express = require("express");
const net = require("net");
const app = express();

const TCP_FORWARD_HOST = "127.0.0.1"; // 転送先TCPサーバのホスト
const TCP_FORWARD_PORT = 6000; // 転送先TCPサーバのポート

app.post(
  "/upload",
  express.raw({ type: "application/octet-stream", limit: "50mb" }),
  (req, res) => {
    try {
      const b64Buffer = req.body;
      console.log(
        "📥 Express が受け取った raw Buffer length:",
        b64Buffer.length
      );
      console.log(`typeof(b64Buffer): ${b64Buffer}`);

      // Base64 をデコードして中身確認
      const b64String = b64Buffer.toString("ascii"); // Base64 は ASCII テキスト
      const decoded = Buffer.from(b64String, "base64").toString("utf8");
      console.log("🔍 デコード結果 (utf-8):", decoded);

      res.status(200).send("OK"); // 先にリクエストを返す

      // 次に送る文字列を作って Base64 エンコード（文字列 => Base64 文字列）
      const nextMsg = "Hello from Node.js Express server!";
      const nextB64String = Buffer.from(nextMsg, "utf8").toString("base64"); // これは base64 文字列
      const nextB64Buffer = Buffer.from(nextB64String, "ascii"); // ASCII bytes として送る

      // 目的のTCPサーバへ送信
      const client = new net.Socket();

      client.connect(TCP_FORWARD_PORT, TCP_FORWARD_HOST, () => {
        client.write(nextB64Buffer, () => {
          console.log("➡️ TCPサーバへ転送完了");
          client.end(); // ✅ 送信完了後に安全に終了
        });

        // client.write(nextB64Buffer);
        // console.log("➡️ 目的のTCPサーバへ転送完了");
        // client.end();　/// データ送信後すぐにで接続を閉じない
      });

      // エラー監視
      client.on("error", (err) => {
        console.error("❌ TCPクライアントエラー:", err.message);
      });

      client.on("close", () => {
        console.log("🔌 TCPクライアント接続を閉じました\n");
      });

      // TCPクライアント接続を閉じた後にレスポンスを返す
    } catch (err) {
      console.error("❌ Express ハンドラエラー:", err);
      res.status(500).send("error");
    }
  }
);

app.listen(3000, () => {
  console.log("🚀 Expressサーバ起動: http://localhost:3000");
});
