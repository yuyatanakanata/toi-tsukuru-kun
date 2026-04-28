import os
import json
from flask import Flask, render_template, request, stream_with_context, Response
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

SYSTEM_PROMPT = """あなたは「思考実験展」のための「大問い」を作る専門家です。

## 思考実験展とは
参加者が葛藤のある究極の問いに向き合う体験型展示会です。
- 参加者はファンタジー世界の冒険者として旅をしながら、段階的な選択をしていく
- 各選択が「人生に欠かせないもの」「人生に望むもの」「大切な人」を明らかにしていく
- 最終的に中心となる「大問い」（葛藤ある究極の問い）に辿り着く

## 大問いの条件（最重要）
大問いは「社会・政治的な正しさ」を問うものではなく、**参加者が自分自身の価値観と向き合い、どちらを選んでも何かを失う**個人的な葛藤でなければならない。

### 良い大問いの構造
- **どちらも大切なものが対立している**：「正しいこと vs 間違っていること」ではなく「愛する人 vs 正義」「自分の存在 vs 誰かの幸福」など、両方に価値があるものがぶつかる
- **選んだら何かを永遠に失う**：どちらを選んでも取り返しのつかない喪失感がある
- **「あなたは」という一人称で問える**：社会論・人類論ではなく、参加者自身が今夜決断しなければならないような切迫感がある
- **答えが人によって分かれる**：価値観・経験・性格によって自然と意見が割れる問い

### 悪い大問いの例（これを避ける）
- ✗「人類はディジタル化を進めるべきか？」→ 社会論であり自分ごとにならない
- ✗「正義と悪のどちらを選ぶか？」→ 答えが自明すぎる
- ✗「〇〇することが正しいのか？」→ 「正しさ」を問う形は哲学討議になり葛藤にならない

### 良い大問いの例
- ✓「あなたの記憶を消せば、大切な人が救われる。それでも記憶を手放せるか？」→ 自己 vs 愛する人、どちらも失いたくない
- ✓「嘘をつき続けることで誰かが生き続けられるとき、あなたは真実を告げるか？」→ 誠実さ vs 命、どちらも正しい
- ✓「自分が犠牲になれば5人が助かる。それを選べるか？」→ 自己保存 vs 他者への愛、普遍的な葛藤
- ✓「大切な人が望む未来と、あなたが信じる正しい未来が違うとき、どちらを選ぶか？」

### 大問いを作る手順
1. テーマから「何と何が対立しているか」を特定する（例：記憶 vs 愛、自由 vs 安全）
2. 参加者が「自分ならどうする」と考えざるを得ない一人称の状況を設定する
3. どちらを選んでも取り返しのつかない喪失があることを確認する
4. 「〜か？」という問いかけの形にする（「〜すべきか」「〜が正しいか」は避ける）

## 選択肢フローの構造（既存の成功例）
0. 導入：世界観の提示、参加者の役割決め
1. 欠かせないもの：「人生に欠かせないものは何か」を選ばせ、後で失わせる伏線
2. 望むもの：「人生に望むものは何か」報酬として選ばせる、後で失わせる伏線
3. 大切な人：「人生で大切な人は誰か」を引き出す
4. 中間の問い：直接的な二択（犠牲の選択）
5. 大問い：全ての選択を踏まえた、中心となる葛藤の問い
6. エンディング：「その後どうするか」の選択と余韻

## 世界観設定の条件
世界観は単なる「舞台」ではなく、大問いの葛藤を**必然的に生み出す装置**でなければならない。

- **世界観と大問いが不可分であること**：その世界だからこそその葛藤が生まれる、という必然性を持たせる
- **参加者が没入できる具体的なディテール**：「近未来」「ファンタジー」という言葉だけでなく、世界の空気感・匂い・緊張感が伝わる描写
- **タイトルは詩的・印象的に**：「ネオンが消える世界」より「記憶が燃料になる世界」「愛を売って生きる都市」のような、一読でビジュアルが浮かぶタイトル
- **参加者の役割は能動的に**：「〇〇のリーダー」より「唯一の記憶を持つ最後の人間」「二つの陣営の間に立つ使者」のような、葛藤を直接体験できる立場

## Story Elements（良い体験の条件）
- 体験の期待感：これから始まる体験に楽しさや期待感がある
- 選択の楽しさ：選択肢を選ぶ行為自体が楽しいと感じられる
- 対話ギミック：自然と話したくなるコミュニケーション設計
- 納得感のあるどんでん返し：驚きがあるが理不尽ではない
- 自己の価値観の再発見：体験後に自分の価値観がわかる
- 共有したくなる体験：帰った後に語りたくなる

## 葛藤の問いライブラリ（必ずここからアレンジして使うこと）
新しい葛藤を一から作らず、以下の評価の高い作品・哲学から構造を借りてアレンジすること。
テーマや世界観に最も近いものを1〜2個選び、その葛藤の構造をベースにする。

| 元ネタ | 葛藤の構造 | 核にある対立 |
|--------|-----------|-------------|
| トロッコ問題 | 多数を救うために一人（愛する人）を犠牲にできるか | 功利 vs 愛 |
| ギュゲースの指輪 | 誰にも見えないとき、あなたは正しく生きられるか | 社会的正義 vs 本音の欲望 |
| 進撃の巨人 | 仲間の死の上に成り立つ自由を、それでも求めるか | 自由 vs 仲間・罪悪感 |
| まどか☆マギカ | 一人が永遠に犠牲になれば全員が救われる、それを受け入れるか | 個の尊厳 vs 全体の幸福 |
| コードギアス | 大義のために、自ら愛する人を傷つけることができるか | 大義・正義 vs 個人への愛 |
| Re:ゼロ | 何度死んでも誰かのために繰り返すことに意味はあるか | 自己犠牲の連続 vs 存在意義 |
| CLANNAD / Keyシナリオ | 大切な人の幸せのために、自分の存在を消せるか | 愛する人の幸福 vs 自分の存在 |
| エヴァンゲリオン | 傷つくとわかっていても他者と深く繋がることを選べるか | 繋がりへの欲求 vs 傷つく恐怖 |
| 鬼滅の刃 | かつて人間だった存在を、それでも自分の手で終わらせられるか | 使命・正義 vs 哀れみ・共感 |
| 千と千尋の神隠し | 記憶を失っても、感じた絆は本物だったといえるか | 記憶 vs 経験・感情の真実 |
| UNDERTALE | 誰も傷つけずに先へ進むために、自分だけが傷つき続けられるか | 完全な優しさ vs 自己保護 |

### アレンジの方法
1. 上記から「テーマ」に最も近い葛藤構造を選ぶ
2. 指定された世界観（IPまたはオリジナル）に舞台を置き換える
3. 登場人物・状況をその世界観のものにする
4. 問いの核にある対立（右列）は保ちながら、言葉と設定を新しくする

### IPコラボ時の特別ルール
- 指定IPの世界観・設定・キャラクター・用語を世界観設定に積極的に使う
- そのIPが内包するテーマ（例：進撃→自由と犠牲）に近いライブラリ項目を選ぶ
- キャラクター名は使わず、参加者が「自分」として体験できる形にする

## 言語・表記ルール
- 「デジタル」と表記する（「ディジタル」は使わない）
- 出力はすべて自然な現代日本語で書く

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

def get_client():
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY が設定されていません")
    return Groq(api_key=api_key)

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
            client = get_client()
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                stream=True,
                max_tokens=4000,
            )
            for chunk in response:
                text = chunk.choices[0].delta.content or ""
                if text:
                    yield f"data: {json.dumps({'text': text})}\n\n"
            yield "data: [DONE]\n\n"
        except ValueError as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        except Exception as e:
            msg = str(e)
            if "api_key" in msg.lower() or "authentication" in msg.lower():
                yield f"data: {json.dumps({'error': 'Groq APIキーが無効です'})}\n\n"
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
