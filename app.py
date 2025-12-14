"""
RFQ Parser Demo Application
===========================
Interactive Streamlit demo with visual components
"""

import streamlit as st
import json
import sys
import time
from datetime import datetime

from rfq_parser import RFQParser, Direction, AssetClass, Urgency

# Page configuration
st.set_page_config(
    page_title="RFQ Parser Demo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better visuals
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A5F;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .json-output {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 5px;
        padding: 1rem;
        font-family: monospace;
        font-size: 0.9rem;
    }
    .direction-buy { color: #28a745; font-weight: bold; }
    .direction-sell { color: #dc3545; font-weight: bold; }
    .direction-twoway { color: #007bff; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


def get_direction_color(direction: Direction) -> str:
    """Get color class for direction"""
    colors = {
        Direction.BUY: "#28a745",
        Direction.SELL: "#dc3545",
        Direction.TWO_WAY: "#007bff",
        Direction.UNKNOWN: "#6c757d"
    }
    return colors.get(direction, "#6c757d")


def get_confidence_color(score: float) -> str:
    """Get color based on confidence score"""
    if score >= 0.8:
        return "#28a745"  # Green
    elif score >= 0.5:
        return "#ffc107"  # Yellow
    else:
        return "#dc3545"  # Red


def main():
    # Header
    st.markdown('<div class="main-header">📊 RFQ Parser Demo</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Parse free-form Request for Quote messages into structured data</div>', unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        use_llm = st.checkbox(
            "Use Mistral LLM",
            value=False,
            help="Enable LLM-powered parsing (requires API key)"
        )
        
        if use_llm:
            api_key = st.text_input(
                "Mistral API Key",
                type="password",
                help="Enter your Mistral API key"
            )
        else:
            api_key = None
            st.info("Using regex-based parsing (no API key required)")
        
        st.divider()
        
        st.header("📝 Sample RFQs")
        sample_rfqs = {
            "FX Spot (Buy)": "Buy 10MM EUR/USD spot",
            "FX Forward": "Need a price on 5M GBP/USD 3M forward",
            "Two-Way": "Can I get a two-way on 50MM USD/JPY?",
            "Urgent Request": "URGENT: Sell 25MM EUR/USD ASAP!",
            "Complex RFQ": "Hi, looking to buy 100 MIO EURUSD 6 months outright, value date IMM Dec"
        }
        
        selected_sample = st.selectbox(
            "Load sample RFQ",
            [""] + list(sample_rfqs.keys())
        )
    
    # Initialize parser
    parser = RFQParser(api_key=api_key, use_llm=use_llm)
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📥 Input")
        
        # Text input
        default_text = sample_rfqs.get(selected_sample, "") if selected_sample else ""
        rfq_text = st.text_area(
            "Enter RFQ Message",
            value=default_text,
            height=150,
            placeholder="e.g., Buy 10MM EUR/USD spot"
        )
        
        parse_button = st.button("🔍 Parse RFQ", type="primary", use_container_width=True)
    
    with col2:
        st.header("📤 Output")
        output_container = st.container()
    
    # Process when button clicked
    if parse_button and rfq_text.strip():
        with st.spinner("Parsing RFQ..."):
            start_time = time.time()
            result = parser.parse(rfq_text)
            parse_time = (time.time() - start_time) * 1000  # ms
        
        with output_container:
            # Key metrics in cards
            metric_cols = st.columns(4)
            
            with metric_cols[0]:
                direction_color = get_direction_color(result.direction)
                st.markdown(f"""
                <div style="background: {direction_color}; padding: 1rem; border-radius: 10px; text-align: center; color: white;">
                    <div style="font-size: 0.8rem; opacity: 0.9;">Direction</div>
                    <div style="font-size: 1.5rem; font-weight: bold;">{result.direction.value}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with metric_cols[1]:
                st.markdown(f"""
                <div style="background: #6c757d; padding: 1rem; border-radius: 10px; text-align: center; color: white;">
                    <div style="font-size: 0.8rem; opacity: 0.9;">Asset Class</div>
                    <div style="font-size: 1.2rem; font-weight: bold;">{result.asset_class.value.replace('_', ' ')}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with metric_cols[2]:
                quantity_display = f"{result.quantity:,.0f}" if result.quantity else "N/A"
                st.markdown(f"""
                <div style="background: #17a2b8; padding: 1rem; border-radius: 10px; text-align: center; color: white;">
                    <div style="font-size: 0.8rem; opacity: 0.9;">Quantity</div>
                    <div style="font-size: 1.2rem; font-weight: bold;">{quantity_display}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with metric_cols[3]:
                conf_color = get_confidence_color(result.confidence_score)
                st.markdown(f"""
                <div style="background: {conf_color}; padding: 1rem; border-radius: 10px; text-align: center; color: white;">
                    <div style="font-size: 0.8rem; opacity: 0.9;">Confidence</div>
                    <div style="font-size: 1.5rem; font-weight: bold;">{result.confidence_score:.0%}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.divider()
            
            # Detailed results
            detail_cols = st.columns(2)
            
            with detail_cols[0]:
                st.subheader("🔍 Parsed Fields")
                
                fields_data = [
                    ("Instrument", result.instrument or "—"),
                    ("Currency Pair", result.currency_pair or "—"),
                    ("Tenor", result.tenor or "—"),
                    ("Settlement Date", result.settlement_date or "—"),
                    ("Strike", str(result.strike) if result.strike else "—"),
                    ("Urgency", result.urgency.value),
                    ("Client", result.client_name or "—"),
                ]
                
                for field, value in fields_data:
                    st.markdown(f"**{field}:** {value}")
            
            with detail_cols[1]:
                st.subheader("📋 JSON Output")
                st.json(result.to_dict())
            
            # Parsing notes
            if result.parsing_notes:
                st.subheader("📝 Parsing Notes")
                for note in result.parsing_notes:
                    st.info(note)
            
            # Performance info
            st.caption(f"⏱️ Parsed in {parse_time:.1f}ms | Mode: {'LLM' if use_llm else 'Regex'}")
    
    elif parse_button:
        st.warning("Please enter an RFQ message to parse.")
    
    # Batch parsing section
    st.divider()
    st.header("📦 Batch Parsing")
    
    with st.expander("Parse Multiple RFQs"):
        batch_input = st.text_area(
            "Enter multiple RFQs (one per line)",
            height=150,
            placeholder="Buy 10MM EURUSD\nSell 5MM GBPUSD\nTwo-way on 20MM USDJPY"
        )
        
        if st.button("Parse Batch", use_container_width=True):
            lines = [line.strip() for line in batch_input.split('\n') if line.strip()]
            if lines:
                results = parser.parse_batch(lines)
                
                # Display as table
                table_data = []
                for r in results:
                    table_data.append({
                        "RFQ": r.raw_text[:50] + "..." if len(r.raw_text) > 50 else r.raw_text,
                        "Direction": r.direction.value,
                        "Asset": r.asset_class.value,
                        "Quantity": f"{r.quantity:,.0f}" if r.quantity else "N/A",
                        "Pair": r.currency_pair or "—",
                        "Confidence": f"{r.confidence_score:.0%}"
                    })
                
                st.dataframe(table_data, use_container_width=True)
    
    # Footer with architecture diagram
    st.divider()
    with st.expander("🏗️ Architecture Overview"):
        st.markdown("""
        ```
        ┌─────────────────────────────────────────────────────────────┐
        │                    RFQ Parser Architecture                  │
        └─────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
        ┌─────────────────────────────────────────────────────────────┐
        │                      Input Layer                            │
        │  • Free-form text (chat, email, voice transcript)           │
        │  • Batch input support                                      │
        └─────────────────────────────────────────────────────────────┘
                                     │
                          ┌──────────┴──────────┐
                          ▼                     ▼
        ┌─────────────────────────┐  ┌─────────────────────────┐
        │     Mistral LLM         │  │    Regex Fallback       │
        │  (Primary Parser)       │  │  (Backup Parser)        │
        │                         │  │                         │
        │  • Semantic understand. │  │  • Pattern matching     │
        │  • Context awareness    │  │  • Fast & reliable      │
        │  • Complex RFQ support  │  │  • No API required      │
        └─────────────────────────┘  └─────────────────────────┘
                          │                     │
                          └──────────┬──────────┘
                                     ▼
        ┌─────────────────────────────────────────────────────────────┐
        │                   ParsedRFQ Object                          │
        │  • Direction (BUY/SELL/TWO_WAY)                             │
        │  • Asset Class, Instrument, Quantity                        │
        │  • Tenor, Settlement Date, Strike                           │
        │  • Confidence Score & Parsing Notes                         │
        └─────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
        ┌─────────────────────────────────────────────────────────────┐
        │                    Output Layer                             │
        │  • JSON serialization                                       │
        │  • API response                                             │
        │  • Trading system integration                               │
        └─────────────────────────────────────────────────────────────┘
        ```
        """)


if __name__ == "__main__":
    main()
