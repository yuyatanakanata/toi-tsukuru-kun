import os
import json
from flask import Flask, render_template, request, stream_with_context, Response
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

SYSTEM_PROMPT = """あなたは「思考実験展」のための「大問い」を作る専門家です。

## 思考実験展とは
参加者が葛藤のある究極の問いに向き合う体験型展示会です。
- 参加者はファンタジー世界の冒険者として旅をしながら、段階的な選択をしていく
- 各選択が「人生に欠かせないもの」「人生に望むもの」「大切な人」を明らかにしていく
- 最終的に中心となる「大問い」（葛藤ある究極の問い）に辿り着く

## 大問いの条件
- 唯一の正解がなく、どちらを選んでも葛藤が残る
- 参加者自身の価値観が反映される
- 「自分ごと」として考えられるリアリティがある
- SNSで共有したくなる余韻が残る
- 前向きなカタルシスがある（暗いだけで終わらない）

## 既存の大問いの例（参考）
- 「誰かのために自分を透明にする（存在を消す）ことが正しい選択か？」（ギュゲースの指輪×トロッコ問題）
- 「自分が犠牲になれば誰かを助けられる時、それを選ぶか？」
- 「大切なものを全て失っても、正しいと信じることを貫けるか？」

## 選択肢フローの構造（既存の成功例）
0. 導入：世界観の提示、参加者の役割決め
1. 欠かせないもの：「人生に欠かせないものは何か」を選ばせ、後で失わせる伏線
2. 望むもの：「人生に望むものは何か」報酬として選ばせる、後で失わせる伏線
3. 大切な人：「人生で大切な人は誰か」を引き出す
4. 中間の問い：直接的な二択（犠牲の選択）
5. 大問い：全ての選択を踏まえた、中心となる葛藤の問い
6. エンディング：「その後どうするか」の選択と余韻

## Story Elements（良い体験の条件）
- 体験の期待感：これから始まる体験に楽しさや期待感がある
- 選択の楽しさ：選択肢を選ぶ行為自体が楽しいと感じられる
- 対話ギミック：自然と話したくなるコミュニケーション設計
- 納得感のあるどんでん返し：驚きがあるが理不尽ではない
- 自己の価値観の再発見：体験後に自分の価値観がわかる
- 共有したくなる体験：帰った後に語りたくなる

## 出力フォーマット
必ず以下のJSON形式のみで出力してください（前後に余分なテキスト不要）：

{
  "大問い": "〇〇か、それとも〇〇か？（葛藤のある究極の問い）",
  "大問いの解説": "この問いに込められた哲学的テーマと葛藤の説明（2-3文）",
  "世界観設定": {
    "タイトル": "世界観のタイトル",
    "概要": "世界観の概要説明（3-4文）",
    "参加者の役割": "参加者がどんな存在として体験するか",
    "世界の核心的な問題": "その世界で起きている根本的な問題"
  },
  "選択肢フロー": [
    {
      "ステージ": "①〇〇",
      "タイトル": "シーンのタイトル",
      "状況説明": "GMが語るナレーション（2-3文）",
      "問い": "参加者への問いかけ",
      "選択肢": ["選択A", "選択B"],
      "大問いへの伏線": "この選択がどう大問いに繋がるかの説明"
    }
  ],
  "GMメモ": {
    "体験のテーマ": "この体験を通じて参加者に感じてほしいこと",
    "盛り上がりどころ": "特に対話が弾むポイント",
    "IPとの接続ポイント": "コラボIPの要素をどこに織り込むか（IPが指定された場合）"
  }
}

IPコラボがある場合、そのIPの世界観・キャラクター・テーマを自然に取り込みながら、
オリジナルの哲学的問いと融合させてください。
"""

def get_model():
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY が設定されていません")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=SYSTEM_PROMPT
    )

@app.route("/")
def index():
    return render_template("index.html")

def extract_file_text(f):
    ext = (f.filename or "").rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        import pypdf
        reader = pypdf.PdfReader(f)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return f.read().decode("utf-8", errors="ignore")

@app.route("/generate", methods=["POST"])
def generate():
    if request.content_type and "multipart/form-data" in request.content_type:
        theme = (request.form.get("theme") or "").strip()
        ip_collab = (request.form.get("ip_collab") or "").strip()
        world_style = (request.form.get("world_style") or "ファンタジー").strip()
        target = (request.form.get("target") or "大人向け").strip()
        notes = (request.form.get("notes") or "").strip()
        uploaded = request.files.get("ref_file")
        file_text = extract_file_text(uploaded) if uploaded and uploaded.filename else ""
    else:
        data = request.json or {}
        theme = (data.get("theme") or "").strip()
        ip_collab = (data.get("ip_collab") or "").strip()
        world_style = (data.get("world_style") or "ファンタジー").strip()
        target = (data.get("target") or "大人向け").strip()
        notes = (data.get("notes") or "").strip()
        file_text = ""

    if not theme:
        return {"error": "テーマ・葛藤の核を入力してください"}, 400

    ref_section = f"\n\n## 参考資料（アップロードされたファイル）\n{file_text[:8000]}" if file_text.strip() else ""

    user_prompt = f"""以下の要件で「大問い」を作成してください。

## 要件
- テーマ・葛藤の核: {theme}
- 世界観の方向性: {world_style}
- ターゲット: {target}
{"- コラボIP: " + ip_collab if ip_collab else ""}
{"- 追加要件: " + notes if notes else ""}{ref_section}

JSON形式のみで出力してください。"""

    def generate_stream():
        try:
            model = get_model()
            response = model.generate_content(user_prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield f"data: {json.dumps({'text': chunk.text})}\n\n"
            yield "data: [DONE]\n\n"
        except ValueError as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        except Exception as e:
            msg = str(e)
            if "API_KEY_INVALID" in msg or "API key" in msg.lower():
                yield f"data: {json.dumps({'error': 'Gemini APIキーが無効です'})}\n\n"
            else:
                yield f"data: {json.dumps({'error': msg})}\n\n"

    return Response(
        stream_with_context(generate_stream()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=False, host="0.0.0.0", port=port)
