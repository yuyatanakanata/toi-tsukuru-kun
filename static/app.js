const form = document.getElementById("generate-form");
const resultSection = document.getElementById("result-section");
const streamingOutput = document.getElementById("streaming-output");
const parsedOutput = document.getElementById("parsed-output");
const submitBtn = document.getElementById("submit-btn");
const copyBtn = document.getElementById("copy-btn");
const refFileInput = document.getElementById("ref-file");
const fileNameDisplay = document.getElementById("file-name-display");
const fileClearBtn = document.getElementById("file-clear-btn");

refFileInput.addEventListener("change", () => {
  if (refFileInput.files[0]) {
    fileNameDisplay.textContent = refFileInput.files[0].name;
    fileClearBtn.style.display = "inline-block";
  }
});

function clearFile() {
  refFileInput.value = "";
  fileNameDisplay.textContent = "企画書・台本などをアップロード";
  fileClearBtn.style.display = "none";
}

document.querySelectorAll('input[name="ip-mode"]').forEach(radio => {
  radio.addEventListener("change", () => {
    document.getElementById("ip-collab-field").style.display =
      radio.value === "collab" ? "block" : "none";
  });
});

let fullText = "";

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  await runGenerate();
});

async function runGenerate() {
  const theme = document.getElementById("theme").value.trim();
  const ipCollab = document.getElementById("ip-collab").value.trim();
  const worldStyle = document.getElementById("world-style").value;
  const target = document.getElementById("target").value;
  const notes = document.getElementById("notes").value.trim();

  if (!theme) {
    showError("テーマ・葛藤の核を入力してください");
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = "生成中...";
  fullText = "";
  streamingOutput.textContent = "";
  parsedOutput.innerHTML = '<div class="loading">AIが考えています</div>';
  resultSection.style.display = "block";
  resultSection.scrollIntoView({ behavior: "smooth", block: "start" });

  try {
    const formData = new FormData();
    formData.append("theme", theme);
    formData.append("ip_collab", ipCollab);
    formData.append("world_style", worldStyle);
    formData.append("target", target);
    formData.append("notes", notes);
    if (refFileInput.files[0]) {
      const file = refFileInput.files[0];
      if (file.size > 5 * 1024 * 1024) {
        showError("ファイルサイズは5MB以下にしてください");
        return;
      }
      formData.append("ref_file", file);
    }

    const response = await fetch("/generate", {
      method: "POST",
      body: formData,
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const data = line.slice(6).trim();
        if (data === "[DONE]") {
          finalize();
          break;
        }
        try {
          const parsed = JSON.parse(data);
          if (parsed.error) {
            showError(parsed.error);
            return;
          }
          if (parsed.text) {
            fullText += parsed.text;
            streamingOutput.textContent = fullText;
          }
        } catch {}
      }
    }
  } catch (err) {
    showError("通信エラー: " + err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "大問いを生成する";
  }
}

function finalize() {
  streamingOutput.textContent = "";
  try {
    const jsonMatch = fullText.match(/\{[\s\S]*\}/);
    if (!jsonMatch) throw new Error("JSONが見つかりません");
    const data = JSON.parse(jsonMatch[0]);
    renderResult(data);
  } catch {
    parsedOutput.innerHTML = `<pre style="white-space:pre-wrap;font-size:0.85rem;color:var(--text-dim)">${escapeHtml(fullText)}</pre>`;
  }
}

function renderResult(data) {
  const big = data["大問い"] || "";
  const desc = data["大問いの解説"] || "";
  const world = data["世界観設定"] || {};
  const stages = data["選択肢フロー"] || [];
  const gm = data["GMメモ"] || {};

  let html = "";

  // 大問い
  html += `<div class="big-question">
    <div class="label">大問い</div>
    <div class="question-text">${escapeHtml(big)}</div>
    <div class="description">${escapeHtml(desc)}</div>
  </div>`;

  // 世界観設定
  html += `<div class="card world-setting">
    <h3>世界観設定</h3>
    <div class="world-title">${escapeHtml(world["タイトル"] || "")}</div>
    <div class="item"><div class="item-label">概要</div><p>${escapeHtml(world["概要"] || "")}</p></div>
    <div class="item"><div class="item-label">参加者の役割</div><p>${escapeHtml(world["参加者の役割"] || "")}</p></div>
    <div class="item"><div class="item-label">世界の核心的な問題</div><p>${escapeHtml(world["世界の核心的な問題"] || "")}</p></div>
  </div>`;

  // 選択肢フロー
  if (stages.length > 0) {
    html += `<div class="card">
      <h3>選択肢フロー</h3>
      <div class="stages">`;
    for (const s of stages) {
      const choices = (s["選択肢"] || []).map(c => `<span class="choice-tag">${escapeHtml(c)}</span>`).join("");
      html += `<div class="stage">
        <div class="stage-title">${escapeHtml(s["ステージ"] || "")} ${escapeHtml(s["タイトル"] || "")}</div>
        <p style="font-size:0.82rem;color:var(--text-dim);margin-bottom:8px">${escapeHtml(s["状況説明"] || "")}</p>
        <div class="stage-question">${escapeHtml(s["問い"] || "")}</div>
        <div class="stage-choices">${choices}</div>
        ${s["大問いへの伏線"] ? `<div class="stage-hint">▷ 伏線: ${escapeHtml(s["大問いへの伏線"])}</div>` : ""}
      </div>`;
    }
    html += `</div></div>`;
  }

  // GMメモ
  if (Object.keys(gm).length > 0) {
    html += `<div class="card gm-memo">
      <h3>GMメモ</h3>
      ${renderMemoItem("体験のテーマ", gm["体験のテーマ"])}
      ${renderMemoItem("盛り上がりどころ", gm["盛り上がりどころ"])}
      ${renderMemoItem("IPとの接続ポイント", gm["IPとの接続ポイント"])}
    </div>`;
  }

  parsedOutput.innerHTML = html;
}

function renderMemoItem(label, value) {
  if (!value) return "";
  return `<div class="memo-item">
    <div class="memo-label">${escapeHtml(label)}</div>
    <div class="memo-text">${escapeHtml(value)}</div>
  </div>`;
}

function showError(msg) {
  parsedOutput.innerHTML = `<div class="error-msg">${escapeHtml(msg)}</div>`;
  streamingOutput.textContent = "";
  resultSection.style.display = "block";
}

function escapeHtml(str) {
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

copyBtn.addEventListener("click", () => {
  const text = parsedOutput.innerText;
  navigator.clipboard.writeText(text).then(() => {
    copyBtn.textContent = "コピーしました！";
    setTimeout(() => (copyBtn.textContent = "コピー"), 2000);
  });
});
