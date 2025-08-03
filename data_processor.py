<<<<<<< HEAD
# In ai-python/data_processor.py

from datetime import datetime

def safe_float(value, default=0.0):
    """Safely convert a value to float, handling None, strings, or numbers."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

=======
# ai-python/data_processor.py

from datetime import datetime

>>>>>>> 3a44620cbe4b768ecfff14a3c9b2eeb499317f71
def process_and_format_data(combined_wallet_data: dict, wallet_address: str):
    metrics = combined_wallet_data.get('metrics', {})
    profile = combined_wallet_data.get('profile', {})
    wallet_nft_transactions_data = combined_wallet_data.get('wallet_nft_transactions', [])
    
<<<<<<< HEAD
    in_txn = int(safe_float(metrics.get('in_txn')))
    out_txn = int(safe_float(metrics.get('out_txn')))
    total_txn = int(safe_float(metrics.get('total_txn')))
    token_cnt = int(safe_float(metrics.get('token_cnt')))
    inflow_addresses = int(safe_float(metrics.get('inflow_addresses')))
    outflow_addresses = int(safe_float(metrics.get('outflow_addresses')))
    wallet_age_days = int(safe_float(metrics.get('wallet_age')))
    washtrade_nft_count_profile = int(safe_float(profile.get('washtrade_nft_count')))
    
    sanction_volume_metrics = safe_float(metrics.get('sanction_volume'))
    mixer_volume_metrics = safe_float(metrics.get('mixer_volume'))
    illicit_volume_metrics = safe_float(metrics.get('illicit_volume'))

=======
    in_txn = int(metrics.get('in_txn', 0))
    out_txn = int(metrics.get('out_txn', 0))
    total_txn = int(metrics.get('total_txn', 0))
    token_cnt = int(metrics.get('token_cnt', 0))
    inflow_addresses = int(metrics.get('inflow_addresses', 0))
    outflow_addresses = int(metrics.get('outflow_addresses', 0))
    sanction_volume_metrics = float(metrics.get('sanction_volume', 0.0))
    mixer_volume_metrics = float(metrics.get('mixer_volume', 0.0))
    illicit_volume_metrics = float(metrics.get('illicit_volume', 0.0))
    wallet_age_days = int(metrics.get('wallet_age', 0))
    washtrade_nft_count_profile = int(profile.get('washtrade_nft_count', 0))
>>>>>>> 3a44620cbe4b768ecfff14a3c9b2eeb499317f71
    aml_is_sanctioned = profile.get('aml_is_sanctioned', False)
    is_shark = profile.get('is_shark', False)
    is_whale = profile.get('is_whale', False)
    is_contract = profile.get('is_contract', False)
<<<<<<< HEAD

    balance_wei_raw = safe_float(metrics.get('balance', '0'))
    balance_eth_raw = balance_wei_raw / 1e18
    balance_usd_raw = safe_float(metrics.get('balance_usd'))
    
    formatted_balance_usd = f"${balance_usd_raw:,.2f}"
    formatted_balance_eth = f"{balance_eth_raw:,.4f} ETH"
=======
    balance_usd_raw = float(metrics.get('balance_usd', 0.0))
    balance_eth_raw = float(metrics.get('balance_eth', 0.0))
    formatted_balance_usd = f"${balance_usd_raw:,.2f}"
    formatted_balance_eth = f"{balance_eth_raw:,.8f} ETH".rstrip('0').rstrip('.') + " ETH"
>>>>>>> 3a44620cbe4b768ecfff14a3c9b2eeb499317f71

    def format_wallet_age(days):
        if days < 30: return f"{days} days"
        if days < 365: return f"{days // 30} months, {days % 30} days"
        return f"{days // 365} years, {(days % 365) // 30} months"
    formatted_age = format_wallet_age(wallet_age_days)

    risk_flags_list = []
<<<<<<< HEAD
    overall_risk_level = "Low Risk"

    if is_shark or mixer_volume_metrics > 0:
        overall_risk_level = "Moderate Risk"
        if is_shark: risk_flags_list.append("Wallet is a 'Shark' (active, high-volume trader).")
        if mixer_volume_metrics > 0: risk_flags_list.append(f"Interacted with coin mixers (${mixer_volume_metrics:,.2f}).")

    if aml_is_sanctioned or sanction_volume_metrics > 0 or is_whale:
        overall_risk_level = "High Risk"
        if is_whale: risk_flags_list.append("Wallet is a 'Whale' (holds significant assets).")
        if aml_is_sanctioned: risk_flags_list.append("Wallet is on a sanctions list.")
        if sanction_volume_metrics > 0: risk_flags_list.append(f"Interacted with sanctioned addresses (${sanction_volume_metrics:,.2f}).")
=======
    if aml_is_sanctioned: risk_flags_list.append("CRITICAL RISK: Wallet is directly sanctioned.")
    if sanction_volume_metrics > 0: risk_flags_list.append(f"HIGH RISK: Interacted with sanctioned addresses.")
    
    overall_risk_level = "Low Risk"
    if any("CRITICAL" in flag for flag in risk_flags_list): overall_risk_level = "High Risk"
    elif any("HIGH" in flag for flag in risk_flags_list): overall_risk_level = "High Risk"
>>>>>>> 3a44620cbe4b768ecfff14a3c9b2eeb499317f71
    
    graph_data = {}
    if in_txn > 0 or out_txn > 0:
        graph_data["transaction_breakdown_chart"] = { "labels": ["Inflow Txns", "Outflow Txns"], "values": [in_txn, out_txn] }

    if sanction_volume_metrics + mixer_volume_metrics + illicit_volume_metrics > 0:
        graph_data["risk_composition_chart"] = { "labels": ["Sanctioned", "Mixer", "Illicit"], "values": [sanction_volume_metrics, mixer_volume_metrics, illicit_volume_metrics] }

    processed_transactions = []
    if isinstance(wallet_nft_transactions_data, list):
        for tx in wallet_nft_transactions_data:
            collection_name = tx.get("collection_name")
            display_name = collection_name if collection_name and collection_name != "N/A" else tx.get("contract_address")
<<<<<<< HEAD
            if display_name:
=======
            if display_name: # Ensure we have some identifier
>>>>>>> 3a44620cbe4b768ecfff14a3c9b2eeb499317f71
                processed_transactions.append({
                    "type": tx.get("transaction_type", "Unknown").capitalize(),
                    "collection_name": display_name,
                    "price_eth": tx.get("price_eth"),
                    "timestamp": tx.get("timestamp")
                })
    
    formatted_metrics = {
        "walletAge": formatted_age, "currentBalanceUsd": formatted_balance_usd, "currentBalanceEth": formatted_balance_eth,
        "totalTransactions": f"{total_txn:,}", "uniqueTokensHeld": f"{token_cnt:,}", "inflowAddresses": f"{inflow_addresses:,}",
        "outflowAddresses": f"{outflow_addresses:,}", "sanctionVolumeMetrics": f"${sanction_volume_metrics:,.2f}",
        "mixerVolumeMetrics": f"${mixer_volume_metrics:,.2f}", "totalWashTradedNfts": f"{washtrade_nft_count_profile:,}",
        "isShark": "Yes" if is_shark else "No", "isWhale": "Yes" if is_whale else "No", "isContract": "Yes" if is_contract else "No",
    }
    
<<<<<<< HEAD
    summary_points = {
        "Wallet Type": "Whale" if is_whale else ("Shark" if is_shark else "Standard"),
        "Primary Risk Factor": risk_flags_list[0] if risk_flags_list else "None Detected",
        "Sanctioned": "Yes" if aml_is_sanctioned else "No",
    }

    clean_report_summary = (
        f"### Whale Profile Summary\n\n"
        f"**Overall Risk Assessment:** {overall_risk_level}\n\n"
        f"This wallet is classified as a **{summary_points['Wallet Type']}**. "
        f"The primary risk factor identified is: **{summary_points['Primary Risk Factor']}**."
    )

    # FIX: Create a much more detailed context summary for the LLM
    context_summary = f"""
- **Core Metrics**:
  - Wallet Age: {formatted_age}
  - Balance (USD): {formatted_balance_usd}
  - Balance (ETH): {formatted_balance_eth}
  - Total Transactions: {total_txn:,}
  - Unique Tokens Held: {token_cnt:,}
  - Inflow Addresses: {inflow_addresses:,}
  - Outflow Addresses: {outflow_addresses:,}

- **Risk & Profile Analysis**:
  - Overall Risk Level: {overall_risk_level}
  - Is Whale: {"Yes" if is_whale else "No"}
  - Is Shark: {"Yes" if is_shark else "No"}
  - Is Sanctioned: {"Yes" if aml_is_sanctioned else "No"}
  - Sanctioned Volume Exposure: ${sanction_volume_metrics:,.2f}
  - Mixer Volume Exposure: ${mixer_volume_metrics:,.2f}
  - Illicit Volume Exposure: ${illicit_volume_metrics:,.2f}
  - Wash Traded NFT Count: {washtrade_nft_count_profile:,}
"""
=======
    context_summary = f"""- Wallet Age: {formatted_age}\n- Balance: {formatted_balance_usd}\n- Transaction Profile: {total_txn} total txns ({in_txn} in, {out_txn} out).\n- AML Status: Sanctioned = {aml_is_sanctioned}\n- Risky Volume Exposure: Sanctioned=${sanction_volume_metrics:,.2f}, Mixer=${mixer_volume_metrics:,.2f}"""
>>>>>>> 3a44620cbe4b768ecfff14a3c9b2eeb499317f71
    human_message_llm_input = {"wallet_address": wallet_address, "context_summary": context_summary}

    return {
        "formatted_metrics": formatted_metrics,
        "overall_risk_level": overall_risk_level,
<<<<<<< HEAD
        "summary_points": summary_points,
        "human_message_llm_input": human_message_llm_input,
        "graph_data": graph_data,
        "transactions": processed_transactions,
        "report": clean_report_summary 
    }
=======
        "human_message_llm_input": human_message_llm_input,
        "graph_data": graph_data,
        "transactions": processed_transactions
    }
>>>>>>> 3a44620cbe4b768ecfff14a3c9b2eeb499317f71
