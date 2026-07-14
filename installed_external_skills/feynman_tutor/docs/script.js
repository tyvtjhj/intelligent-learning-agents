/* ===== Feynman Tutor · demo stage ===== */
const DEMOS = {
  dns: {
    q: "帮我理解一下 DNS 到底是怎么回事，我基础为零",
    analogy: "<b>DNS</b>（域名系统）就是 <b>互联网的电话簿</b> 📒。你只记得住 <code>google.com</code> 这种名字，但机器之间靠一串数字地址找彼此。你一问名字，它把对应的数字地址翻给你——名字翻成数字，这就是它干的唯一一件事。",
    art:
`  📱 "google.com 地址多少?"
     │
     ▼ 先问家里的路由器(兼任小电话簿)
  🛜 "我没存…去问运营商的大电话簿"
     │
     ▼
  🏢 运营商DNS ──一路接力问到权威源──▶ 答案回 📱`,
    ledger: [["🆕 DNS", "Domain Name System", "互联网电话簿，名字翻成数字地址"]]
  },
  fourier: {
    q: "我数学很烂，能不能从零帮我理解傅里叶变换",
    analogy: "<b>傅里叶变换</b> 就是 <b>把一段和弦拆回单个音符</b> 🎵。任何复杂的波，都能拆成一堆纯正弦波之和。听上去是一团混响，傅里叶帮你看清「里面到底有哪几个纯音、各占多少」。",
    art:
`  复杂波形            拆解成纯正弦波之和
  ∿╲╱∿╲    ═══▶    ︵      +   ∿∿∿    +   ·····
   ╲╱  ╲             低频(粗)     中频        高频(细)
  "一团混响"          "看清里面有哪几个纯音"`,
    ledger: [["🆕 傅里叶变换", "Fourier Transform", "把任意波拆成一堆纯正弦波之和"]]
  },
  compound: {
    q: "复利到底厉害在哪，我想真正搞懂不是背公式",
    analogy: "<b>复利</b> 就是 <b>滚雪球</b> ❄️。普通利息只在本金上算；复利是「利息也会生利息」——雪球滚的过程中，沾上的雪又变成球的一部分，继续沾更多雪。所以时间越久，后期增长越陡。",
    art:
`  单利(只本金生息)   复利(利滚利)
  ▓                  ▓
  ▓▓                 ▓▓
  ▓▓▓                ▓▓▓▓
  ▓▓▓▓               ▓▓▓▓▓▓▓▓
  ▓▓▓▓▓              ▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ◄ 越往后越陡`,
    ledger: [["🆕 复利", "Compound Interest", "利息再生利息，越滚越快（滚雪球）"]]
  },
  backprop: {
    q: "帮我搞懂神经网络的反向传播是怎么回事，基础为零",
    analogy: "<b>反向传播</b> 就是 <b>追责到每个环节</b> 🔍。网络猜错了，从「最终错了多少」倒着往回推：每一个旋钮（参数）该为这次错误担多少责任？担责多的多调一点。如此反复，慢慢逼近正确。",
    art:
`  正向：输入 ──▶ 层1 ──▶ 层2 ──▶ 输出 → 比对答案
                                          │ 错了多少?
  反向：每个旋钮该担多少责 ◀──────────────┘
        ◀── 倒推回每一层，按责任微调旋钮 ──`,
    ledger: [
      ["🆕 反向传播", "Backpropagation", "从最终误差倒推，给每个参数分配「责任」再微调"],
      ["🆕 梯度", "Gradient", "某个旋钮往哪个方向调、调多少，能最快减小误差"]
    ]
  }
};

const qEl = document.getElementById("demoQ");
const aEl = document.getElementById("demoAnalogy");
const artEl = document.getElementById("demoArt");
const ledgerEl = document.getElementById("demoLedger");

function render(key){
  const d = DEMOS[key];
  if(!d) return;
  qEl.textContent = d.q;
  // retrigger fade animation
  aEl.style.animation = "none"; artEl.style.animation = "none";
  void aEl.offsetWidth;
  aEl.style.animation = ""; artEl.style.animation = "";
  aEl.innerHTML = d.analogy;
  artEl.textContent = d.art;
  ledgerEl.innerHTML = d.ledger
    .map(r => `<tr><td>${r[0]}</td><td>${r[1]}</td><td>${r[2]}</td></tr>`)
    .join("");
}

document.getElementById("demoPicker").addEventListener("click", e => {
  const btn = e.target.closest(".chip");
  if(!btn) return;
  document.querySelectorAll("#demoPicker .chip").forEach(c => c.classList.remove("is-active"));
  btn.classList.add("is-active");
  render(btn.dataset.key);
});

// initial
render("dns");

/* ===== copy buttons + toast ===== */
const toast = document.getElementById("toast");
let toastTimer;
function showToast(){
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 1600);
}
document.querySelectorAll(".copy").forEach(btn => {
  btn.addEventListener("click", async () => {
    const text = btn.getAttribute("data-copy");
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = text; document.body.appendChild(ta); ta.select();
      document.execCommand("copy"); document.body.removeChild(ta);
    }
    showToast();
  });
});
