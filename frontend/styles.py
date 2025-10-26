"""
CSS styles and JavaScript for the Streamlit application
"""

BACKGROUND_CSS = """
<style>
:root {
    --glass-bg: rgba(6, 18, 32, 0.65);
    --glass-border: rgba(142, 228, 175, 0.25);
    --accent: #32f47a;
    --accent-dark: #0b3d21;
}

/* Hide Streamlit's default page navigation */
[data-testid="stSidebarNav"] {
    display: none !important;
}

[data-testid="stToolbar"] {
    background: transparent !important;
}

[data-testid="stCollapsedControl"] button {
    border: none !important;
    background: rgba(5, 15, 27, 0.78) !important;
    color: #f3fbff !important;
}

[data-testid="stStatusWidget"] {
    display: none !important;
}

[data-testid="stHeaderActionContainer"] button[title="View fullscreen"],
[data-testid="stHeaderActionContainer"] button[title="Rerun"] {
    display: none !important;
}

.stApp {
    background: transparent;
    color: #f5f9ff;
}

.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    background: url('https://images.hdqwalls.com/download/graph-web-abstract-4k-hn-1920x1080.jpg') no-repeat center center fixed;
    background-size: cover;
    z-index: -2;
    animation: hueShift 16s linear infinite;
    filter: hue-rotate(0deg) saturate(1.1);
}

.stApp::after {
    content: "";
    position: fixed;
    inset: 0;
    background: radial-gradient(circle at 20% 20%, rgba(46, 255, 146, 0.15), transparent 45%),
                radial-gradient(circle at 80% 10%, rgba(46, 186, 255, 0.12), transparent 40%),
                linear-gradient(135deg, rgba(2, 12, 22, 0.6), rgba(0, 0, 0, 0.75));
    z-index: -1;
    backdrop-filter: blur(2px);
}

@keyframes hueShift {
    0% { filter: hue-rotate(0deg) saturate(1.1); }
    50% { filter: hue-rotate(180deg) saturate(1.3); }
    100% { filter: hue-rotate(360deg) saturate(1.1); }
}

.hero-intro {
    text-align: center;
    display: flex;
    flex-direction: column;
    gap: 1.1rem;
    align-items: center;
    margin-bottom: 1.5rem;
}

.hero-intro h1 {
    font-size: clamp(2.6rem, 5vw, 3.4rem);
    font-weight: 700;
    letter-spacing: 0.015em;
    margin: 0;
}

.hero-intro p {
    font-size: 1.1rem;
    line-height: 1.6;
    max-width: 36rem;
    color: rgba(228, 247, 238, 0.85);
}

main .block-container {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: 28px;
    padding: 3.5rem 3rem 4rem;
    box-shadow: 0 35px 80px rgba(0, 0, 0, 0.55);
    backdrop-filter: blur(18px);
    max-width: 720px;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.8rem;
    background: rgba(4, 14, 18, 0.6);
    padding: 0.6rem;
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.stTabs [data-baseweb="tab"] {
    background: rgba(255, 255, 255, 0.06);
    border-radius: 14px;
    color: #f2f9ff;
    font-weight: 600;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: rgba(50, 244, 122, 0.22);
    color: #0b1f12;
    box-shadow: inset 0 0 0 1px rgba(50, 244, 122, 0.45);
}

.stDownloadButton > button {
    background: linear-gradient(120deg, #2a9df4, #1cf6cf);
    color: #031421;
    border: none;
    border-radius: 999px;
    padding: 0.55rem 1.4rem;
    font-weight: 600;
}

.stDownloadButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 18px 36px rgba(28, 246, 207, 0.35);
}

.stProgress > div > div > div {
    background: linear-gradient(90deg, #32f47a, #29c6f0);
}

main .block-container h1,
main .block-container h2,
main .block-container h3,
main .block-container p,
main .block-container label,
main .block-container span,
main .block-container .stMarkdown,
main .block-container .st-success,
main .block-container .st-warning,
main .block-container .st-error {
    color: #f3f8ff !important;
}

[data-testid="stSidebar"] {
    background: rgba(5, 15, 27, 0.78) !important;
    backdrop-filter: blur(18px);
    border-right: 1px solid rgba(142, 228, 175, 0.18);
}

[data-testid="stSidebar"] * {
    color: #f3fbff !important;
}

[data-baseweb="radio"] div[role="radiogroup"]>div {
    background: rgba(255, 255, 255, 0.04);
    border-radius: 14px;
    padding: 0.4rem 0.6rem;
}

[data-baseweb="radio"] label {
    border-radius: 10px;
    padding: 0.35rem 0.8rem;
}

[data-baseweb="radio"] label[data-checked="true"] {
    background: rgba(50, 244, 122, 0.25);
    border: 1px solid rgba(50, 244, 122, 0.35);
}

div[data-baseweb="input"] {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 18px;
    border: 1px solid rgba(255, 255, 255, 0.18);
    transition: border 0.2s ease, box-shadow 0.2s ease;
}

div[data-baseweb="input"]:focus-within {
    border-color: rgba(50, 244, 122, 0.55);
    box-shadow: 0 8px 24px rgba(50, 244, 122, 0.15);
}

div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea {
    color: #f7fbff !important;
}

textarea {
    background: rgba(255, 255, 255, 0.04) !important;
    border-radius: 18px !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    color: #f7fbff !important;
}

.stButton>button {
    width: 100%;
    border-radius: 999px;
    padding: 0.6rem 1.2rem;
    background: linear-gradient(120deg, #2bf06f, #1bc861);
    color: #04130a;
    font-weight: 600;
    letter-spacing: 0.02em;
    border: none;
    box-shadow: 0 18px 32px rgba(41, 224, 113, 0.25);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 26px 40px rgba(41, 224, 113, 0.35);
}

.stButton>button:active {
    transform: translateY(0);
}

.st-bw {
    background-color: rgba(4, 18, 15, 0.45) !important;
}

.st-alert {
    border-radius: 16px;
    background-color: rgba(13, 33, 24, 0.65);
}

@media (max-width: 768px) {
    main .block-container {
        padding: 2.4rem 1.6rem 3rem;
        margin: 2.4rem 0;
    }
}
</style>
"""

ENTER_NAVIGATION_JS = """
<script>
const hideApplyHints = () => {
    const candidates = [
        ...document.querySelectorAll('[data-testid="textInputInstructions"]'),
        ...document.querySelectorAll('[data-testid="stTooltipLabel"]'),
    ];
    candidates.forEach(el => {
        if (el && typeof el.textContent === 'string' && el.textContent.toLowerCase().includes('press enter to apply')) {
            el.style.display = 'none';
        }
        if (el && el.parentElement && el.parentElement.getAttribute('aria-label') === 'Press Enter to apply') {
            el.parentElement.style.display = 'none';
        }
    });
};

const triggerPrimaryButton = (startEl) => {
    if (!startEl) {
        startEl = document.activeElement;
    }
    const container = startEl ? startEl.closest('[data-testid="stVerticalBlock"]') : null;
    const searchScope = container || document;
    const buttons = Array.from(searchScope.querySelectorAll('button'));
    const preferredLabels = ['login', 'register', 'submit', 'continue', 'save', 'load'];
    const match = buttons.find((btn) => {
        const text = (btn.innerText || '').trim().toLowerCase();
        if (!text) return false;
        if (preferredLabels.includes(text)) return true;
        return btn.getAttribute('kind') === 'primary';
    });
    if (match) {
        match.click();
        return true;
    }
    return false;
};

const attachEnterHandlers = () => {
    const inputs = Array.from(document.querySelectorAll('input[type=text], input[type=email], input[type=password]'));
    inputs.forEach((input, index) => {
        if (input.dataset.enterHandlerBound === 'true') {
            return;
        }
        input.dataset.enterHandlerBound = 'true';
        input.addEventListener('keydown', (event) => {
            if (event.key !== 'Enter') {
                return;
            }

            const next = inputs[index + 1];
            if (next) {
                event.preventDefault();
                next.focus();
                return;
            }

            if (triggerPrimaryButton(input)) {
                event.preventDefault();
            }
        }, { once: false });
    });
};

const combinedObserver = new MutationObserver(() => {
    hideApplyHints();
    attachEnterHandlers();
});

combinedObserver.observe(document.body, { childList: true, subtree: true });
hideApplyHints();
attachEnterHandlers();
</script>
"""
