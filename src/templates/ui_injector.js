(function() {
    if (window.__agyVoiceBtnVersion === 10) return "already_injected";
    window.__agyVoiceBtnVersion = 10;
    window.__agyVoiceBtnInjected = true;

    if (window.__agyVoiceInterval) {
        clearInterval(window.__agyVoiceInterval);
        window.__agyVoiceInterval = null;
    }
    if (window.__agyVoiceObserver) {
        window.__agyVoiceObserver.disconnect();
        window.__agyVoiceObserver = null;
    }

    // Clean up any legacy floating pills and v5 buttons
    const oldPill = document.getElementById("agy-floating-plan-pill");
    if (oldPill) oldPill.remove();
    document.querySelectorAll('.agy-doc-plan-btn').forEach(function(b) {
        if (!b.querySelector('.agy-doc-plan-label')) b.remove();
    });
    document.querySelectorAll('.agy-inline-plan-btn').forEach(function(b) {
        if ((b.textContent || '').trim() === 'Voz') b.remove();
    });

    const SPEAKER_PATH = "M560-131v-82q90-26 145-100t55-168q0-94-55-168T560-749v-82q124 28 202 125.5T840-481q0 127-78 224.5T560-131ZM120-360v-240h160l200-200v640L280-360H120Zm440 40v-322q47 22 73.5 66t26.5 96q0 51-26.5 94.5T560-320ZM400-606l-86 86H200v80h114l86 86v-252ZM300-480Z";
    const PAUSE_PATH = "M520-200v-560h240v560H520Zm-320 0v-560h240v560H200Zm400-80h80v-400h-80v400Zm-320 0h80v-400h-80v400Zm0-400v400-400Zm320 0v400-400Z";
    const PLAY_PATH = "M320-200v-560l440 280-440 280Zm80-280Zm0 134 210-134-210-134v268Z";
    const RESTART_PATH = "M480-80q-75 0-140.5-28.5t-114-77q-48.5-48.5-77-114T120-440h80q0 117 81.5 198.5T480-160q117 0 198.5-81.5T760-440q0-117-81.5-198.5T480-720h-6l62 62-56 58-160-160 160-160 56 58-62 62h6q75 0 140.5 28.5t114 77q48.5 48.5 77 114T840-440q0 75-28.5 140.5t-77 114q-48.5 48.5-114 77T480-80Z";

    function getConvId() {
        try {
            const loc = window.location.pathname + window.location.search + window.location.hash;
            let m = loc.match(/\/c\/([a-zA-Z0-9_-]{8,})/);
            if (m) return m[1];
            m = loc.match(/cascadeId=([a-zA-Z0-9_-]{8,})/);
            if (m) return m[1];
            m = loc.match(/brain[\/\\]([a-zA-Z0-9_-]{8,})/);
            if (m) return m[1];
            return null;
        } catch (e) { return null; }
    }

    function getPlanPath() {
        try {
            const loc = window.location.pathname + window.location.search + window.location.hash;
            const m = loc.match(/uri=([^&]+)/);
            if (m) {
                return decodeURIComponent(decodeURIComponent(m[1])).replace(/^file:\/\/\/?/, '');
            }
        } catch (e) {}
        return null;
    }

    function createSvgIcon(pathData, size) {
        if (!size) size = 16;
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("width", String(size));
        svg.setAttribute("height", String(size));
        svg.setAttribute("viewBox", "0 -960 960 960");
        svg.setAttribute("fill", "currentColor");
        svg.setAttribute("class", "agy-voice-icon");
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", pathData);
        svg.appendChild(path);
        return svg;
    }

    function setBtnIcon(btn, pathData, size) {
        while (btn.firstChild) btn.removeChild(btn.firstChild);
        btn.appendChild(createSvgIcon(pathData, size || 16));
    }

    function getTextSig(text) {
        return (text || "").toLowerCase().replace(/[^a-z0-9áéíóúñü]+/g, "").slice(0, 60);
    }

    function setBtnState(btn, restartBtn, state) {
        btn.dataset.voiceState = state;
        if (state === "playing") {
            setBtnIcon(btn, PAUSE_PATH, 16);
            btn.style.color = "#38bdf8";
            btn.title = "Pausar lectura de voz";
            if (restartBtn) restartBtn.style.display = "inline-flex";
        } else if (state === "paused") {
            setBtnIcon(btn, PLAY_PATH, 16);
            btn.style.color = "#4ade80";
            btn.title = "Continuar lectura desde donde se quedó";
            if (restartBtn) restartBtn.style.display = "inline-flex";
        } else {
            setBtnIcon(btn, SPEAKER_PATH, 16);
            btn.style.color = "";
            btn.title = "Leer respuesta en voz alta (J.A.R.V.I.S.)";
            if (restartBtn) restartBtn.style.display = "none";
        }
    }

    function extractTurnText(copyBtn) {
        try {
            const footer = copyBtn.closest('.pt-3') || (copyBtn.parentElement && copyBtn.parentElement.parentElement && copyBtn.parentElement.parentElement.parentElement && copyBtn.parentElement.parentElement.parentElement.parentElement);
            let body = (footer && footer.previousElementSibling) ? footer.previousElementSibling : null;
            if (!body) {
                body = copyBtn.closest('[role="article"][aria-label="Agent response"]') || 
                       (footer && footer.parentElement && footer.parentElement.querySelector('[role="article"][aria-label="Agent response"]'));
            }
            if (body) {
                let blocks = Array.from(body.querySelectorAll('.px-2.py-1')).filter(function(el) {
                    if (el.closest('button')) return false;
                    if (el.closest('[data-testid="worked-for-collapsible"]')) return false;
                    let p = el.parentElement;
                    while (p && p !== body) {
                        const prev = p.previousElementSibling;
                        if (prev && prev.tagName === 'BUTTON' && (prev.hasAttribute('aria-expanded') || prev.getAttribute('data-testid') === 'worked-for-collapsible')) {
                            return false;
                        }
                        p = p.parentElement;
                    }
                    return true;
                });

                if (blocks.length === 0) {
                    const clone = body.cloneNode(true);
                    clone.querySelectorAll('style, script, button, .select-none, [data-testid="worked-for-collapsible"]').forEach(function(s) { s.remove(); });
                    clone.querySelectorAll('pre').forEach(function(pre) {
                        pre.textContent = ' [He incluido un bloque de código en pantalla]. ';
                    });
                    const fullText = (clone.textContent || '').trim();
                    if (fullText && fullText !== 'User cancelled agent execution.') {
                        return fullText;
                    }
                }

                const texts = blocks.map(function(b) {
                    const clone = b.cloneNode(true);
                    clone.querySelectorAll('style, script, button, .select-none').forEach(function(s) { s.remove(); });
                    clone.querySelectorAll('pre').forEach(function(pre) {
                        pre.textContent = ' [He incluido un bloque de código en pantalla]. ';
                    });
                    return (clone.textContent || '').trim();
                }).filter(function(t) { return t && t !== 'User cancelled agent execution.'; });
                if (texts.length > 0) {
                    return texts.join('\n\n');
                }
            }
        } catch (e) {}
        return "";
    }

    function removeFloatingPlanPill() {
        const pill = document.getElementById("agy-floating-plan-pill");
        if (pill) pill.remove();
    }

    function injectArtifactCardButtons() {
        // Antigravity 2.0 artifact list rows
        const rows = document.querySelectorAll('[data-testid="artifact-row"]');
        rows.forEach(function(row) {
            if (row.querySelector('.agy-row-plan-btn')) return;
            const text = (row.textContent || '').toLowerCase();
            const title = (row.title || '').toLowerCase();
            const isPlan = text.includes('plan') || title.includes('plan') || text.includes('.md');
            if (!isPlan) return;

            const btn = document.createElement("span");
            btn.className = "agy-row-plan-btn";
            btn.style.display = "inline-flex";
            btn.style.alignItems = "center";
            btn.style.justifyContent = "center";
            btn.style.marginLeft = "auto";
            btn.style.padding = "2px 7px";
            btn.style.borderRadius = "6px";
            btn.style.background = "rgba(14, 165, 233, 0.2)";
            btn.style.border = "1px solid rgba(56, 189, 248, 0.6)";
            btn.style.color = "#38bdf8";
            btn.style.fontSize = "11px";
            btn.style.fontWeight = "600";
            btn.style.cursor = "pointer";
            btn.style.gap = "4px";
            btn.title = "Escuchar este plan con voz IA (Ctrl + Alt + P)";
            btn.appendChild(createSvgIcon(SPEAKER_PATH, 12));

            const lbl = document.createElement("span");
            lbl.className = "agy-row-plan-label";
            lbl.textContent = "Leer";
            btn.appendChild(lbl);

            btn.addEventListener("click", async function(e) {
                e.preventDefault();
                e.stopPropagation();
                if (btn.dataset.isBusy === "1") return;
                btn.dataset.isBusy = "1";
                setTimeout(function() { delete btn.dataset.isBusy; }, 600);
                try {
                    await fetch("http://127.0.0.1:49152/plan/speak", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ action: "toggle", conv_id: getConvId() })
                    });
                } catch (err) {}
            });

            row.appendChild(btn);
        });

        // Webview artifact cards
        const cards = document.querySelectorAll('.artifact-card');
        cards.forEach(function(card) {
            if (card.querySelector('.agy-inline-plan-btn')) return;
            const uriBtn = card.querySelector('[data-uri]');
            const dataUri = uriBtn ? (uriBtn.getAttribute('data-uri') || '') : '';
            const text = (card.textContent || '').toLowerCase();
            const isPlan = dataUri.toLowerCase().includes('plan') || text.includes('plan') || dataUri.toLowerCase().endsWith('.md');
            if (!isPlan) return;

            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "agy-inline-plan-btn";
            btn.style.display = "inline-flex";
            btn.style.alignItems = "center";
            btn.style.gap = "6px";
            btn.style.padding = "3px 10px";
            btn.style.marginTop = "6px";
            btn.style.borderRadius = "9999px";
            btn.style.background = "rgba(14, 165, 233, 0.16)";
            btn.style.border = "1px solid rgba(56, 189, 248, 0.6)";
            btn.style.color = "#38bdf8";
            btn.style.fontSize = "12px";
            btn.style.fontWeight = "600";
            btn.style.cursor = "pointer";
            btn.style.transition = "all 0.15s ease";
            btn.title = "Escuchar este plan con voz IA (Ctrl + Alt + P)";
            btn.appendChild(createSvgIcon(SPEAKER_PATH, 13));

            const s = document.createElement("span");
            s.textContent = "Escuchar Plan";
            btn.appendChild(s);

            btn.addEventListener("click", async function(e) {
                e.preventDefault();
                e.stopPropagation();
                if (btn.dataset.isBusy === "1") return;
                btn.dataset.isBusy = "1";
                setTimeout(function() { delete btn.dataset.isBusy; }, 600);

                let planPath = null;
                if (dataUri) {
                    planPath = decodeURIComponent(dataUri.replace(/^file:\/\/\/?/, ''));
                }
                try {
                    await fetch("http://127.0.0.1:49152/plan/speak", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ action: "toggle", plan_path: planPath, conv_id: getConvId() })
                    });
                } catch (err) {}
            });

            card.appendChild(btn);
        });
    }

    function injectTabPlanButtons() {
        const tabs = document.querySelectorAll('[data-tab-id*="plan.md"], [data-tab-id*="Plan"], [data-tab-id*="plan"]');
        tabs.forEach(function(tab) {
            const parent = tab.parentElement;
            if (!parent || parent.querySelector('.agy-tab-plan-btn')) return;

            const dataTabId = tab.getAttribute('data-tab-id') || '';
            let planPath = null;
            const m = dataTabId.match(/file:\/\/\/?([^"]+)/);
            if (m) {
                planPath = decodeURIComponent(decodeURIComponent(m[1]));
            }

            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "agy-tab-plan-btn agy-button inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold cursor-pointer border-none";
            btn.style.marginLeft = "8px";
            btn.style.background = "#0284c7";
            btn.style.border = "1px solid #38bdf8";
            btn.style.color = "#ffffff";
            btn.style.height = "26px";
            btn.style.boxShadow = "0 1px 3px rgba(0,0,0,0.2)";
            btn.title = "Escuchar este archivo de plan con voz IA (Ctrl + Alt + P)";
            btn.appendChild(createSvgIcon(SPEAKER_PATH, 13));

            const lbl = document.createElement("span");
            lbl.className = "agy-tab-plan-label";
            lbl.textContent = "Escuchar Plan";
            btn.appendChild(lbl);

            btn.addEventListener("click", async function(e) {
                e.preventDefault();
                e.stopPropagation();
                if (btn.dataset.isBusy === "1") return;
                btn.dataset.isBusy = "1";
                setTimeout(function() { delete btn.dataset.isBusy; }, 600);
                try {
                    await fetch("http://127.0.0.1:49152/plan/speak", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ action: "toggle", plan_path: planPath, conv_id: getConvId() })
                    });
                } catch (err) {}
            });

            parent.insertBefore(btn, tab.nextSibling);
        });
    }

    function injectDocumentPlanButtons() {
        const mdRoots = document.querySelectorAll('[data-markdown-root]');
        mdRoots.forEach(function(root) {
            if (root.querySelector('.agy-doc-plan-btn')) return;
            const h1 = root.querySelector('h1');
            if (!h1) return;
            const txt = (h1.textContent || '').toLowerCase();
            const isPlan = txt.includes('plan') || txt.includes('implementaci');
            if (!isPlan) return;

            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "agy-doc-plan-btn agy-button inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-semibold cursor-pointer border-none my-2";
            btn.style.background = "#0284c7";
            btn.style.border = "1px solid #38bdf8";
            btn.style.color = "#ffffff";
            btn.style.boxShadow = "0 1px 3px rgba(0,0,0,0.2)";
            btn.title = "Escuchar este plan con voz IA (Ctrl + Alt + P)";
            btn.appendChild(createSvgIcon(SPEAKER_PATH, 13));

            const lbl = document.createElement("span");
            lbl.className = "agy-doc-plan-label";
            lbl.textContent = "Escuchar Plan";
            btn.appendChild(lbl);

            btn.addEventListener("click", async function(e) {
                e.preventDefault();
                e.stopPropagation();
                if (btn.dataset.isBusy === "1") return;
                btn.dataset.isBusy = "1";
                setTimeout(function() { delete btn.dataset.isBusy; }, 600);
                try {
                    await fetch("http://127.0.0.1:49152/plan/speak", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ action: "toggle", plan_path: getPlanPath(), conv_id: getConvId() })
                    });
                } catch (err) {}
            });

            h1.parentElement.insertBefore(btn, h1.nextSibling);
        });
    }

    function injectReviewProceedButtons() {
        const candidates = document.querySelectorAll('.review-button, button');
        candidates.forEach(function(btn) {
            const txt = (btn.textContent || '').trim();
            if (!/^(Review|Proceed|Review\s*v)$/i.test(txt)) return;
            const parent = btn.parentElement;
            if (!parent || parent.querySelector('.agy-header-plan-btn')) return;

            const agyBtn = document.createElement("button");
            agyBtn.type = "button";
            agyBtn.className = "agy-header-plan-btn agy-button agy-button-xs inline-flex items-center font-medium transition-colors select-none outline-none cursor-pointer justify-center border-none h-6 text-xs rounded-md gap-1 px-2.5 mr-2";
            agyBtn.style.display = "inline-flex";
            agyBtn.style.alignItems = "center";
            agyBtn.style.gap = "5px";
            agyBtn.style.padding = "3px 10px";
            agyBtn.style.marginRight = "6px";
            agyBtn.style.marginLeft = "2px";
            agyBtn.style.borderRadius = "6px";
            agyBtn.style.background = "#0284c7";
            agyBtn.style.border = "1px solid #38bdf8";
            agyBtn.style.color = "#ffffff";
            agyBtn.style.fontSize = "12px";
            agyBtn.style.fontWeight = "600";
            agyBtn.style.cursor = "pointer";
            agyBtn.title = "Escuchar plan de implementación con voz IA (Ctrl + Alt + P)";
            agyBtn.appendChild(createSvgIcon(SPEAKER_PATH, 13));

            const label = document.createElement("span");
            label.className = "agy-header-plan-label";
            label.textContent = "Escuchar Plan";
            agyBtn.appendChild(label);

            agyBtn.addEventListener("click", async function(e) {
                e.preventDefault();
                e.stopPropagation();
                if (agyBtn.dataset.isBusy === "1") return;
                agyBtn.dataset.isBusy = "1";
                setTimeout(function() { delete agyBtn.dataset.isBusy; }, 600);
                try {
                    await fetch("http://127.0.0.1:49152/plan/speak", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ action: "toggle", plan_path: getPlanPath(), conv_id: getConvId() })
                    });
                } catch (err) {}
            });

            parent.insertBefore(agyBtn, btn);
        });
    }

    function injectButtons() {
        removeFloatingPlanPill();
        injectArtifactCardButtons();
        injectTabPlanButtons();
        injectDocumentPlanButtons();
        injectReviewProceedButtons();

        const copyBtns = document.querySelectorAll('button[aria-label="Copy"], button[aria-label="Copied"]');
        copyBtns.forEach(function(copyBtn) {
            const parent = copyBtn.parentElement;
            if (!parent) return;
            const isResponseFooter = copyBtn.closest('.pt-3') || parent.querySelector('button[aria-label="Good response"]');
            if (!isResponseFooter) return;
            if (parent.querySelector('.agy-voice-replay-btn')) return;

            if (!copyBtn.dataset.agyTurnId) {
                copyBtn.dataset.agyTurnId = 'turn_' + Math.random().toString(36).slice(2, 9) + '_' + Date.now();
            }
            const turnId = copyBtn.dataset.agyTurnId;

            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = (copyBtn.className || '') + ' agy-voice-replay-btn';
            btn.setAttribute('aria-label', 'Leer en voz alta');
            btn.dataset.agyTurnId = turnId;

            const restartBtn = document.createElement('button');
            restartBtn.type = 'button';
            restartBtn.className = (copyBtn.className || '') + ' agy-voice-restart-btn';
            restartBtn.setAttribute('aria-label', 'Reiniciar lectura');
            restartBtn.title = 'Reiniciar lectura desde el principio';
            restartBtn.dataset.agyTurnId = turnId;
            setBtnIcon(restartBtn, RESTART_PATH, 16);
            restartBtn.style.display = "none";

            setBtnState(btn, restartBtn, "idle");

            btn.addEventListener('click', async function(e) {
                e.preventDefault();
                e.stopPropagation();

                if (btn.dataset.isBusy === "1") return;
                btn.dataset.isBusy = "1";
                setTimeout(function() { delete btn.dataset.isBusy; }, 600);

                window.__agyActiveTurnId = turnId;
                const text = extractTurnText(copyBtn);
                setBtnState(btn, restartBtn, "playing");

                document.querySelectorAll('.agy-voice-replay-btn').forEach(function(other) {
                    if (other !== btn) {
                        const otherRestart = other.parentElement && other.parentElement.querySelector('.agy-voice-restart-btn');
                        setBtnState(other, otherRestart, "idle");
                    }
                });

                try {
                    const res = await fetch('http://127.0.0.1:49152/speak', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ text: text, action: 'toggle', turn_id: turnId })
                    });
                    const data = await res.json();
                    if (data.state === "paused") {
                        setBtnState(btn, restartBtn, "paused");
                    } else if (data.state === "playing") {
                        setBtnState(btn, restartBtn, "playing");
                    } else {
                        setBtnState(btn, restartBtn, "idle");
                        if (window.__agyActiveTurnId === turnId) window.__agyActiveTurnId = null;
                    }
                } catch (err) {
                    setBtnState(btn, restartBtn, "idle");
                    if (window.__agyActiveTurnId === turnId) window.__agyActiveTurnId = null;
                }
            });

            restartBtn.addEventListener('click', async function(e) {
                e.preventDefault();
                e.stopPropagation();

                if (restartBtn.dataset.isBusy === "1") return;
                restartBtn.dataset.isBusy = "1";
                setTimeout(function() { delete restartBtn.dataset.isBusy; }, 600);

                window.__agyActiveTurnId = turnId;
                const text = extractTurnText(copyBtn);
                setBtnState(btn, restartBtn, "playing");

                try {
                    await fetch('http://127.0.0.1:49152/speak', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ text: text, restart: true, turn_id: turnId })
                    });
                    setBtnState(btn, restartBtn, "playing");
                } catch (err) {
                    setBtnState(btn, restartBtn, "idle");
                    if (window.__agyActiveTurnId === turnId) window.__agyActiveTurnId = null;
                }
            });

            parent.insertBefore(btn, copyBtn);
            parent.insertBefore(restartBtn, copyBtn);
        });
    }

    if (window.__agyVoiceInterval) clearInterval(window.__agyVoiceInterval);
    window.__agyVoiceInterval = setInterval(async function() {
        injectButtons();
        try {
            const res = await fetch('http://127.0.0.1:49152/status');
            const data = await res.json();
            const srvState = data.is_paused ? "paused" : (data.is_playing ? "playing" : "idle");
            const activeTurnId = data.turn_id || window.__agyActiveTurnId || "";
            const srvSig = data.sig || "";

            const allBtns = Array.from(document.querySelectorAll('.agy-voice-replay-btn'));
            let matchedBtn = null;

            if (srvState !== "idle") {
                if (activeTurnId) {
                    matchedBtn = allBtns.find(function(b) { return b.dataset.agyTurnId === activeTurnId; });
                }
                if (!matchedBtn && srvSig) {
                    for (let i = allBtns.length - 1; i >= 0; i--) {
                        const b = allBtns[i];
                        const cBtn = b.parentElement && b.parentElement.querySelector('button[aria-label="Copy"], button[aria-label="Copied"]');
                        if (cBtn) {
                            const sig = getTextSig(extractTurnText(cBtn));
                            if (sig && (sig.startsWith(srvSig.slice(0, 35)) || srvSig.startsWith(sig.slice(0, 35)))) {
                                matchedBtn = b;
                                if (b.dataset.agyTurnId) window.__agyActiveTurnId = b.dataset.agyTurnId;
                                break;
                            }
                        }
                    }
                }
            } else {
                window.__agyActiveTurnId = null;
            }

            allBtns.forEach(function(b) {
                const rBtn = b.parentElement && b.parentElement.querySelector('.agy-voice-restart-btn');
                if (srvState === "idle") {
                    setBtnState(b, rBtn, "idle");
                } else if (b === matchedBtn) {
                    setBtnState(b, rBtn, srvState);
                } else {
                    setBtnState(b, rBtn, "idle");
                }
            });

            const convId = getConvId();
            const planUrl = convId ? `http://127.0.0.1:49152/plan/status?conv_id=${encodeURIComponent(convId)}` : 'http://127.0.0.1:49152/plan/status';
            const planRes = await fetch(planUrl);
            const planData = await planRes.json();
            removeFloatingPlanPill();
            const planBtns = document.querySelectorAll('.agy-header-plan-btn, .agy-tab-plan-btn, .agy-doc-plan-btn');
            planBtns.forEach(function(hBtn) {
                let hLabel = hBtn.querySelector('.agy-header-plan-label, .agy-tab-plan-label, .agy-doc-plan-label, .agy-plan-btn-label');
                let labelText = "Escuchar Plan";
                let iconPath = SPEAKER_PATH;
                let bg = "#0284c7";
                let border = "#38bdf8";
                let title = "Escuchar plan de implementación con voz IA (Ctrl + Alt + P)";

                if (planData.is_reading_plan && planData.is_playing && !planData.is_paused) {
                    bg = "#059669";
                    border = "#34d399";
                    title = "Pausar narración del plan (Ctrl + Alt + P)";
                    labelText = "Pausar Plan";
                    iconPath = PAUSE_PATH;
                } else if (planData.is_reading_plan && planData.is_paused) {
                    bg = "#d97706";
                    border = "#fbbf24";
                    title = "Continuar narración del plan (Ctrl + Alt + P)";
                    labelText = "Continuar Plan";
                    iconPath = PLAY_PATH;
                }

                hBtn.style.background = bg;
                hBtn.style.borderColor = border;
                hBtn.title = title;
                setBtnIcon(hBtn, iconPath, 13);
                if (!hLabel) {
                    hLabel = document.createElement("span");
                    hLabel.className = "agy-plan-btn-label";
                }
                hLabel.textContent = labelText;
                hBtn.appendChild(hLabel);
            });
        } catch (e) {}
    }, 600);

    if (window.__agyVoiceObserver) window.__agyVoiceObserver.disconnect();
    const obs = new MutationObserver(function() { injectButtons(); });
    window.__agyVoiceObserver = obs;
    if (document.body) {
        obs.observe(document.body, { childList: true, subtree: true });
        injectButtons();
    } else {
        window.addEventListener('DOMContentLoaded', function() {
            obs.observe(document.body, { childList: true, subtree: true });
            injectButtons();
        });
    }
    return "injected";
})();
