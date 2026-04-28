"""
プロンプト検証スクリプト
使い方: python test_prompt.py
GROQ_API_KEY が環境変数に必要（.envファイルから自動読み込み）
"""
import os, json, sys
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

TEST_CASES = [
    {
        "name": "ブルーアーカイブ × 自己犠牲",
        "theme": "自己犠牲と仲間への愛",
        "world_style": "学園もの",
        "target": "大人向け（20〜30代）",
        "ip_collab": "ブルーアーカイブ",
        "notes": "",
    },
    {
        "name": "オリジナル × 記憶と存在",
        "theme": "記憶と存在のアイデンティティ",
        "world_style": "SF・近未来",
        "target": "大人向け（20〜30代）",
        "ip_collab": "",
        "notes": "",
    },
    {
        "name": "進撃の巨人 × 自由と犠牲",
        "theme": "自由のために仲間を犠牲にできるか",
        "world_style": "ダークファンタジー",
        "target": "大人向け（20〜30代）",
        "ip_collab": "進撃の巨人",
        "notes": "",
    },
]

# app.pyと同じSYSTEM_PROMPTをインポート
sys.path.insert(0, os.path.dirname(__file__))
from app import SYSTEM_PROMPT

def build_prompt(case):
    ip_collab = case["ip_collab"]
    ip_instruction = f"""
## IPコラボ指定: {ip_collab}
このIPの世界観を深く取り込むこと。
- {ip_collab}の固有名詞（地名・組織・概念・用語）を世界観設定に必ず使う
- {ip_collab}のファンが「これはあの世界だ」と感じられる描写にする
- {ip_collab}が持つ中心テーマ・葛藤をベースに、葛藤ライブラリから最も近い構造を選んでアレンジする
""" if ip_collab else ""

    return f"""以下の要件で「大問い」を作成してください。

## 要件
- テーマ・葛藤の核: {case['theme']}
- 世界観の方向性: {case['world_style']}
- ターゲット: {case['target']}
{"- コラボIP: " + ip_collab if ip_collab else "- 世界観: オリジナル（IPなし）"}{ip_instruction}
{"- 追加要件: " + case['notes'] if case['notes'] else ""}

## 必須条件
- 選択肢フローは必ず①〜⑥の6ステージ作成すること
- 大問いは「あなたは〜するか？」という一人称の個人的な葛藤にすること
- 葛藤ライブラリから最も近い構造を選んでアレンジすること

JSON形式のみで出力してください。"""

def evaluate(name, data):
    results = []
    big_q = data.get("大問い", "")
    stages = data.get("選択肢フロー", [])
    world = data.get("世界観設定", {})

    # 大問いの質チェック
    if "あなた" in big_q:
        results.append("✅ 大問い: 一人称（あなた）形式")
    else:
        results.append("❌ 大問い: 一人称になっていない")

    ng_words = ["正しい", "すべき", "べきか", "すべきか"]
    found_ng = [w for w in ng_words if w in big_q]
    if found_ng:
        results.append(f"❌ 大問い: 「{'・'.join(found_ng)}」→議論になる。「できるか」「選べるか」に変える")
    else:
        results.append("✅ 大問い: 「すべき/べきか」なし。個人の葛藤として問えている")

    # ステージ数チェック
    stage_count = len(stages)
    if stage_count >= 5:
        results.append(f"✅ ステージ数: {stage_count}段階")
    elif stage_count >= 3:
        results.append(f"⚠️  ステージ数: {stage_count}段階（5〜6推奨）")
    else:
        results.append(f"❌ ステージ数: {stage_count}段階（少なすぎる）")

    # IP固有名詞チェック（IPありの場合）
    if "ブルーアーカイブ" in name:
        ip_keywords = ["キヴォトス", "ヘイロー", "シャーレ", "先生", "生徒会"]
        world_text = json.dumps(world, ensure_ascii=False)
        found = [k for k in ip_keywords if k in world_text]
        if found:
            results.append(f"✅ BA固有名詞: {found}")
        else:
            results.append(f"❌ BA固有名詞なし（期待: {ip_keywords}）")
    elif "進撃" in name:
        ip_keywords = ["壁", "調査兵団", "巨人", "パラディ", "エレン"]
        world_text = json.dumps(world, ensure_ascii=False)
        found = [k for k in ip_keywords if k in world_text]
        if found:
            results.append(f"✅ 進撃固有名詞: {found}")
        else:
            results.append(f"❌ 進撃固有名詞なし（期待: {ip_keywords}）")

    return results

def analyze_quality(data):
    """大問いとフローの質を定性的に分析して解説する"""
    lines = []
    big_q = data.get("大問い", "")
    stages = data.get("選択肢フロー", [])

    lines.append("\n【流れの質・分析】")

    # ① 大問いの葛藤構造
    conflict_pairs = [
        (["犠牲", "失う", "諦める"], ["救う", "守る", "残す"],
         "「何かを失う」と「何かを守る」の対立。どちらも大切だから葛藤になる"),
        (["真実", "正直", "告げる"], ["嘘", "隠す", "守る"],
         "「誠実さ」と「愛する人を守ること」の対立。どちらも正しいから苦しい"),
        (["自分", "自己", "アイデンティティ"], ["他者", "仲間", "誰か", "愛する"],
         "「自分を保つこと」と「他者への愛」の対立。自己保存vs利他の普遍的葛藤"),
        (["使命", "役割", "義務", "責任"], ["愛", "愛する", "大切", "感情"],
         "「社会的な使命」と「個人的な愛」の対立。どちらも捨てられないから葛藤になる"),
        (["記憶", "過去", "アイデンティティ"], ["存在", "未来", "今", "命"],
         "「自分が自分であること」と「大切な人の存在」の対立。アイデンティティの根本的な問い"),
        (["自由", "解放"], ["犠牲", "仲間", "絆", "命"],
         "「自由への渇望」と「仲間への愛・責任」の対立。どちらも人間の根源的な欲求"),
    ]
    found_conflict = False
    for a_words, b_words, reason in conflict_pairs:
        a = [w for w in a_words if w in big_q]
        b = [w for w in b_words if w in big_q]
        if a and b:
            lines.append(f"  ✅ 葛藤の対立: 「{'・'.join(a)}」vs「{'・'.join(b)}」")
            lines.append(f"     → {reason}")
            found_conflict = True
            break
    if not found_conflict:
        lines.append("  ❌ 葛藤の対立: 大問いに2つの価値の衝突が見えない")
        lines.append("     → 良い大問いは「どちらも大切なものが対立」している必要がある")
        lines.append(f"     → 現在の大問い: 「{big_q[:60]}...」")
        lines.append("     → 改善案: 「〇〇を手放すか、それとも〇〇を失うか」という構造にする")

    # ② 「すべき」「べきか」チェック（全ステージ＋大問い）
    ng_words = ["すべき", "べきか", "すべきか"]
    subeki_stages = []
    for i, s in enumerate(stages):
        q = s.get("問い", "")
        found = [w for w in ng_words if w in q]
        if found:
            subeki_stages.append(f"ステージ{i+1}「{q[:35]}...」({'/'.join(found)})")
    if big_q and any(w in big_q for w in ng_words):
        subeki_stages.insert(0, f"大問い「{big_q[:35]}...」")
    if subeki_stages:
        lines.append(f"  ❌ 「すべき/べきか」表現: {len(subeki_stages)}箇所で検出")
        for s in subeki_stages[:4]:
            lines.append(f"     → {s}")
        lines.append("     → 「すべき」は議論・正論になる。「できるか」「選べるか」に変えると個人の葛藤になる")
    else:
        lines.append("  ✅ 表現: 全ステージ・大問いで「すべき/べきか」なし。個人の葛藤として問えている")

    # ③ 同じ問いの繰り返しチェック
    questions = [s.get("問い", "") for s in stages]
    seen = {}
    duplicates = []
    for i, q in enumerate(questions):
        key = q[:20]
        if key in seen:
            duplicates.append(f"ステージ{seen[key]+1}とステージ{i+1}が類似")
        else:
            seen[key] = i
    if duplicates:
        lines.append(f"  ❌ 問いの重複: {', '.join(duplicates)}")
        lines.append("     → 各ステージは異なる角度から葛藤に近づくべき。同じ問いの繰り返しは体験が単調になる")
    else:
        lines.append("  ✅ 問いの多様性: 各ステージで異なる問いが設定されている")

    # ④ 伏線回収チェック（序盤の感情・価値観が終盤に使われているか）
    early_text = " ".join(s.get("問い", "") + s.get("状況説明", "") for s in stages[:2])
    late_text = " ".join(s.get("問い", "") + s.get("状況説明", "") for s in stages[-2:])
    value_words = ["大切", "欠かせない", "望む", "愛", "仲間", "命", "自由", "記憶", "存在"]
    early_values = [w for w in value_words if w in early_text]
    late_values = [w for w in value_words if w in late_text]
    overlap = set(early_values) & set(late_values)
    if overlap:
        lines.append(f"  ✅ 伏線回収: 序盤で引き出した「{'・'.join(overlap)}」が終盤の葛藤に繋がっている")
        lines.append("     → 「あのときの選択が今の葛藤に繋がる」構造が成立している")
    else:
        lines.append("  ❌ 伏線回収: 序盤と終盤が連動していない")
        lines.append("     → 序盤で「大切なもの」を選ばせ、それを終盤で脅かす設計が必要")
        lines.append(f"     → 序盤のキーワード: {early_values} / 終盤のキーワード: {late_values}")

    # ⑤ 感情的な山場の位置チェック
    emotional_words = ["愛", "失う", "犠牲", "覚悟", "絆", "命", "悲しみ", "孤独"]
    stage_scores = [sum(1 for w in emotional_words if w in s.get("状況説明","") + s.get("問い","")) for s in stages]
    peak = max(range(len(stage_scores)), key=lambda i: stage_scores[i]) + 1 if stage_scores else 0
    if peak >= len(stages) - 1:
        lines.append(f"  ✅ 感情の山場: ステージ{peak}（終盤）が最も感情的→クライマックスに向けて盛り上がる構成")
    elif peak > 0:
        lines.append(f"  ⚠️  感情の山場: ステージ{peak}（中盤）がピーク→終盤に向けてさらに高まる設計が望ましい")
    else:
        lines.append("  ❌ 感情的山場なし: 感情を揺さぶる描写が全体的に不足している")

    return "\n".join(lines)

def main():
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        print("❌ GROQ_API_KEY が設定されていません")
        sys.exit(1)

    client = Groq(api_key=api_key)

    # 引数でケース番号を指定可能（例: python3 test_prompt.py 0）
    target = int(sys.argv[1]) if len(sys.argv) > 1 else None
    cases = [TEST_CASES[target]] if target is not None else TEST_CASES

    for case in cases:
        print(f"\n{'='*60}")
        print(f"テストケース: {case['name']}")
        print('='*60)

        prompt = build_prompt(case)
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                stream=False,
                max_tokens=8000,
            )
        except Exception as e:
            if "rate_limit" in str(e).lower() or "429" in str(e):
                print(f"⏸️  レート制限に達しました。しばらく待ってから再実行してください。")
                print(f"   残りのテストケースはスキップします。")
                break
            raise

        raw = response.choices[0].message.content
        json_match = __import__("re").search(r'\{[\s\S]*\}', raw)
        if not json_match:
            print("❌ JSONパース失敗")
            print(raw[:500])
            continue

        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            print(f"❌ JSONデコードエラー: {e}")
            continue

        print(f"\n【大問い】\n{data.get('大問い', '')}")
        print(f"\n【世界観タイトル】\n{data.get('世界観設定', {}).get('タイトル', '')}")
        print(f"\n【ステージ一覧】")
        for s in data.get("選択肢フロー", []):
            print(f"  {s.get('ステージ','')} {s.get('タイトル','')}")
            print(f"    問い: {s.get('問い','')}")

        print(f"\n【自動評価】")
        for r in evaluate(case["name"], data):
            print(f"  {r}")

        print(analyze_quality(data))

if __name__ == "__main__":
    main()
