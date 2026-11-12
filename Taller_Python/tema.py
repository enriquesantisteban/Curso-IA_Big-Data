import streamlit as st


def aplicar_tema() -> None:
    st.markdown(
        """
        <style>
          :root {
            color-scheme: light !important;
            --text-color: #172b43;
            --background-color: #f3f7fb;
            --secondary-background-color: #ffffff;
            --primary-color: #2878d0;
            --lgne-ink: #17324f;
            --lgne-blue: #2878d0;
            --lgne-cyan: #35a6c8;
            --lgne-green: #28a47a;
            --lgne-line: #dfe8f1;
            --lgne-muted: #687d92;
          }
          [data-testid="stAppViewContainer"] {
            background: radial-gradient(ellipse at 8% 0%, #eaf5ff 0, transparent 34%),
                        linear-gradient(180deg, #f7faff 0%, #f3f7fb 100%);
            color: #172b43 !important;
          }
          [data-testid="stHeader"] { background: rgba(247,250,255,.88); }
          [data-testid="stMainBlockContainer"] {
            max-width: 1540px;
            padding-top: 1.6rem;
            padding-bottom: 2.5rem;
          }
          h1, h2, h3 { color: #142b45 !important; letter-spacing: -.025em; }
          h1 { font-weight: 760; }
          h2 { font-weight: 690; }
          p, label, [data-testid="stCaptionContainer"],
          [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"] {
            color: #253a50 !important;
            opacity: 1 !important;
          }
          [data-testid="stCaptionContainer"] { color: #40576e !important; }
          [data-testid="stWidgetLabel"] p { color: #213950 !important; font-size: 15px; font-weight: 620; }
          [data-testid="stCaptionContainer"] p { color: #40576e !important; font-size: 14px; }
          input::placeholder, textarea::placeholder { color: #596f85 !important; opacity: 1 !important; }
          [data-testid="stMetric"] {
            min-height: 112px;
            padding: 17px 19px;
            border: 1px solid var(--lgne-line);
            border-left: 4px solid var(--lgne-blue);
            border-radius: 15px;
            background: linear-gradient(145deg, #fff 20%, #f3f8ff 100%);
            box-shadow: 0 5px 18px rgba(34, 75, 120, .07);
          }
          [data-testid="stMetricLabel"] p {
            color: #425c76 !important;
            font-size: .8rem;
            font-weight: 680;
            letter-spacing: .01em;
          }
          [data-testid="stMetricValue"] {
            color: #142b45 !important;
            font-size: clamp(1.25rem, 1.7vw, 1.9rem);
            font-weight: 740;
            line-height: 1.2;
          }
          [data-testid="stMetricDelta"] { font-weight: 650; }
          [data-testid="stHorizontalBlock"] [data-testid="column"]:nth-child(2) [data-testid="stMetric"] { border-left-color: var(--lgne-cyan); }
          [data-testid="stHorizontalBlock"] [data-testid="column"]:nth-child(3) [data-testid="stMetric"] { border-left-color: var(--lgne-green); }
          [data-testid="stHorizontalBlock"] [data-testid="column"]:nth-child(4) [data-testid="stMetric"] { border-left-color: #e5a63a; }
          [data-testid="stHorizontalBlock"] [data-testid="column"]:nth-child(5) [data-testid="stMetric"] { border-left-color: #8b70ca; }
          [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--lgne-line) !important;
            border-radius: 16px !important;
            background: rgba(255,255,255,.94);
            box-shadow: 0 5px 18px rgba(34,75,120,.055);
          }
          [data-testid="stForm"] {
            border: 1px solid var(--lgne-line);
            border-radius: 16px;
            padding: 1.25rem 1.35rem;
            background: linear-gradient(155deg, #fff 45%, #f7fbff 100%);
            box-shadow: 0 5px 18px rgba(34,75,120,.055);
          }
          [data-testid="stBaseButton-primary"] {
            color: #fff !important;
            border: 0;
            border-radius: 10px;
            background: linear-gradient(115deg, #2776cf, #35a2c6);
            font-weight: 680;
            box-shadow: 0 4px 12px rgba(39,118,207,.2);
          }
          [data-testid="stBaseButton-primary"]:hover {
            color: #fff !important;
            border: 0;
            background: linear-gradient(115deg, #1e65b4, #238bab);
          }
          [data-testid="stBaseButton-secondary"],
          [data-testid="stDownloadButton"] button {
            border-radius: 10px;
            border-color: #cbd9e7;
            font-weight: 620;
          }
          [data-testid="stDownloadButton"] button {
            color: #135b99 !important;
            background: #edf6ff;
          }
          [data-testid="stBaseButton-secondary"] { color: #243b52 !important; background: #fff; }
          [data-testid="stTextInput"] input,
          [data-testid="stNumberInput"] input,
          [data-testid="stDateInput"] input,
          [data-testid="stSelectbox"] [role="combobox"],
          [data-testid="stTextArea"] textarea {
            border-color: #d5e1ed;
            border-radius: 9px;
            background: #fff;
            color: #172b43 !important;
          }
          [data-testid="stTextInput"] input,
          [data-testid="stNumberInput"] input,
          [data-testid="stDateInput"] input,
          [data-testid="stSelectbox"] [role="combobox"] { color: #172b43 !important; }
          [data-testid="stTopNav"] a,
          [data-testid="stTopNav"] button { color: #1e3853 !important; font-weight: 650; }
          [data-testid="stDataFrame"], [data-testid="stDataEditor"] {
            border: 1px solid #e1eaf3;
            border-radius: 12px;
            overflow: hidden;
            background: #ffffff !important;
            color: #172b43 !important;
            --gdg-bg-cell: #ffffff;
            --gdg-bg-cell-medium: #f6f9fc;
            --gdg-bg-header: #eaf2fb;
            --gdg-bg-header-has-focus: #d9eaff;
            --gdg-bg-header-hasFocus: #d9eaff;
            --gdg-bg-header-hovered: #e1efff;
            --gdg-text-dark: #172b43;
            --gdg-text-medium: #314a64;
            --gdg-text-light: #4d657e;
            --gdg-accent-color: #2878d0;
            --gdg-accent-light: #e2f0ff;
            --gdg-accent-fg: #ffffff;
            --gdg-border-color: #dce6ef;
            --gdg-horizontal-border-color: #e5edf4;
            --gdg-link-color: #145fa7;
          }
          [data-testid="stAlert"] { border-radius: 12px; }
          [data-testid="stExpander"] {
            border-color: #dce7f1;
            border-radius: 12px;
            background: #fbfdff;
          }
          [data-testid="stTopNav"] { border-bottom: 1px solid #e1eaf3; }
        </style>
        """,
        unsafe_allow_html=True,
    )
