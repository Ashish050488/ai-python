from datetime import datetime

def safe_float(value, default=0.0):
    """Safely convert a value to float, handling None, strings, or numbers."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def process_and_format_data(combined_wallet_data: dict, wallet_address: str):
    metrics = combined_wallet_data.get('metrics', {})
    profile = combined_wallet_data.get('profile', {})
    wallet_nft_transactions_data = combined_wallet_data.get('wallet_nft_transactions', [])
    
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

    aml_is_sanctioned = profile.get('aml_is_sanctioned', False)
    is_shark = profile.get('is_shark', False)
    is_whale = profile.get('is_whale', False)
    is_contract = profile.get('is_contract', False)

    balance_wei_raw = safe_float(metrics.get('balance', '0'))
    balance_eth_raw = balance_wei_raw / 1e18
    balance_usd_raw = safe_float(metrics.get('balance_usd'))
    
    formatted_balance_usd = f"${balance_usd_raw:,.2f}"
    formatted_balance_eth = f"{balance_eth_raw:,.4f} ETH"

    def format_wallet_age(days):
        if days < 30: return f"{days} days"
        if days < 365: return f"{days // 30} months, {days % 30} days"
        return f"{days // 365} years, {(days % 365) // 30} months"
    formatted_age = format_wallet_age(wallet_age_days)

    # --- FIX: More robust risk assessment logic ---
    risk_flags_list = []
    overall_risk_level = "Low Risk" 

    # Define conditions for escalating risk
    if is_shark or mixer_volume_metrics > 0:
        overall_risk_level = "Moderate Risk"
        if is_shark: risk_flags_list.append("Wallet is a 'Shark' (active, high-volume trader).")
        if mixer_volume_metrics > 0: risk_flags_list.append(f"Interacted with coin mixers (${mixer_volume_metrics:,.2f}).")

    # A wallet is ALWAYS High Risk if it's a whale, sanctioned, or simply has a very high balance.
    if aml_is_sanctioned or sanction_volume_metrics > 0 or is_whale or balance_usd_raw > 1000000:
        overall_risk_level = "High Risk"
        if balance_usd_raw > 1000000 and not is_whale: risk_flags_list.append("Wallet holds a significant balance (over $1M USD).")
        if is_whale: risk_flags_list.append("Wallet is classified as a 'Whale' by the API.")
        if aml_is_sanctioned: risk_flags_list.append("Wallet is on a sanctions list.")
        if sanction_volume_metrics > 0: risk_flags_list.append(f"Interacted with sanctioned addresses (${sanction_volume_metrics:,.2f}).")
    # --- END OF FIX ---
    
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
            if display_name:
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
    human_message_llm_input = {"wallet_address": wallet_address, "context_summary": context_summary}

    return {
        "formatted_metrics": formatted_metrics,
        "overall_risk_level": overall_risk_level,
        "summary_points": summary_points,
        "human_message_llm_input": human_message_llm_input,
        "graph_data": graph_data,
        "transactions": processed_transactions,
        "report": clean_report_summary 
    }