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

def process_and_format_data(combined_wallet_data: dict, wallet_address: str):
    metrics = combined_wallet_data.get('metrics', {})
    profile = combined_wallet_data.get('profile', {})
    wallet_nft_transactions_data = combined_wallet_data.get('wallet_nft_transactions', [])
    
    # Use the safe_float helper for all numeric conversions
    in_txn = int(safe_float(metrics.get('in_txn')))
    out_txn = int(safe_float(metrics.get('out_txn')))
    total_txn = int(safe_float(metrics.get('total_txn')))
    token_cnt = int(safe_float(metrics.get('token_cnt')))
    inflow_addresses = int(safe_float(metrics.get('inflow_addresses')))
    outflow_addresses = int(safe_float(metrics.get('outflow_addresses')))
    wallet_age_days = int(safe_float(metrics.get('wallet_age')))
    washtrade_nft_count_profile = int(safe_float(profile.get('washtrade_nft_count')))

    # Handle risk metrics safely
    sanction_volume_metrics = safe_float(metrics.get('sanction_volume'))
    mixer_volume_metrics = safe_float(metrics.get('mixer_volume'))
    illicit_volume_metrics = safe_float(metrics.get('illicit_volume'))

    # Check for boolean flags
    aml_is_sanctioned = profile.get('aml_is_sanctioned', False)
    is_shark = profile.get('is_shark', False)
    is_whale = profile.get('is_whale', False)
    is_contract = profile.get('is_contract', False)

    # FIX: Correctly convert balances from wei (smallest unit) to ETH
    # The API provides balance in wei as a string, so we convert it and divide by 10**18
    balance_wei_raw = safe_float(metrics.get('balance', '0'))
    balance_eth_raw = balance_wei_raw / 1e18 # 1 ETH = 10^18 Wei
    
    # Use a separate API field for USD value if available, or calculate it
    balance_usd_raw = safe_float(metrics.get('balance_usd'))
    
    formatted_balance_usd = f"${balance_usd_raw:,.2f}"
    formatted_balance_eth = f"{balance_eth_raw:,.4f} ETH"

    def format_wallet_age(days):
        if days < 30: return f"{days} days"
        if days < 365: return f"{days // 30} months, {days % 30} days"
        return f"{days // 365} years, {(days % 365) // 30} months"
    formatted_age = format_wallet_age(wallet_age_days)

    # Re-evaluate risk based on correctly parsed data
    risk_flags_list = []
    if aml_is_sanctioned: risk_flags_list.append("CRITICAL RISK: Wallet is directly sanctioned.")
    if sanction_volume_metrics > 0: risk_flags_list.append(f"HIGH RISK: Interacted with sanctioned addresses (${sanction_volume_metrics:,.2f}).")
    
    overall_risk_level = "Low Risk" # Default
    if any("CRITICAL" in flag for flag in risk_flags_list) or any("HIGH" in flag for flag in risk_flags_list):
        overall_risk_level = "High Risk"
    
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
    
    context_summary = f"""- Wallet Age: {formatted_age}\n- Balance: {formatted_balance_usd}\n- Transaction Profile: {total_txn} total txns ({in_txn} in, {out_txn} out).\n- AML Status: Sanctioned = {aml_is_sanctioned}\n- Risky Volume Exposure: Sanctioned=${sanction_volume_metrics:,.2f}, Mixer=${mixer_volume_metrics:,.2f}"""
    human_message_llm_input = {"wallet_address": wallet_address, "context_summary": context_summary}

    return {
        "formatted_metrics": formatted_metrics,
        "overall_risk_level": overall_risk_level,
        "human_message_llm_input": human_message_llm_input,
        "graph_data": graph_data,
        "transactions": processed_transactions
    }