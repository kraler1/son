"""
BIST Strategy Backtesting Module
Stratejilerin geçmiş veriler üzerindeki getirisini, başarı oranını ve risk metriklerini simüle eder.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from src.indicators import add_all_indicators


def run_backtest(
    df: pd.DataFrame,
    initial_capital: float = 100000.0,
    commission_rate: float = 0.001,  # Binde 1 komisyon
    stop_loss_pct: float = 4.0,       # %4 Stop-Loss
    take_profit_pct: float = 8.0,     # %8 Kar Al
    strategy_mode: str = "Ağırlıklı Çoklu İndikatör"
) -> Dict[str, Any]:
    """
    Geçmiş BIST verisi üzerinde simülasyon çalıştırır.
    """
    if df is None or len(df) < 50:
        return {"error": "Backtest için en az 50 günlük veri gereklidir."}

    df = add_all_indicators(df)
    
    cash = initial_capital
    position = 0          # Eldeki hisse adedi
    entry_price = 0.0
    entry_date = None
    trades: List[Dict[str, Any]] = []
    equity_curve: List[Dict[str, Any]] = []

    # Günlük simülasyon döngüsü
    for i in range(30, len(df)):
        current_date = df.index[i]
        close = float(df['Close'].iloc[i])
        high = float(df['High'].iloc[i])
        low = float(df['Low'].iloc[i])
        
        rsi = df['RSI'].iloc[i]
        macd = df['MACD'].iloc[i]
        macd_sig = df['MACD_Signal'].iloc[i]
        ema21 = df['EMA_21'].iloc[i]
        ema50 = df['EMA_50'].iloc[i]
        st_dir = df['Supertrend_Direction'].iloc[i]
        
        # Sinyal Koşulları
        buy_signal = False
        sell_signal = False

        if strategy_mode == "Trend Takipçisi (EMA & Supertrend)":
            buy_signal = (close > ema21 > ema50) and (st_dir == 1)
            sell_signal = (close < ema21) or (st_dir == -1)
            
        elif strategy_mode == "Dip/Tepe Avcısı (RSI & Bollinger)":
            bb_lower = df['BB_Lower'].iloc[i]
            bb_upper = df['BB_Upper'].iloc[i]
            buy_signal = (rsi < 35) or (low <= bb_lower)
            sell_signal = (rsi > 68) or (high >= bb_upper)
            
        elif strategy_mode == "MACD Kesişimi":
            prev_macd = df['MACD'].iloc[i-1]
            prev_sig = df['MACD_Signal'].iloc[i-1]
            buy_signal = (prev_macd <= prev_sig) and (macd > macd_sig)
            sell_signal = (prev_macd >= prev_sig) and (macd < macd_sig)
            
        else:  # "Ağırlıklı Çoklu İndikatör" (Varsayılan)
            score = 0
            if rsi < 35: score += 20
            elif rsi > 68: score -= 20
            
            if macd > macd_sig: score += 20
            else: score -= 20
            
            if close > ema21: score += 20
            else: score -= 20
            
            if st_dir == 1: score += 20
            else: score -= 20

            buy_signal = (score >= 40)
            sell_signal = (score <= -20)

        # Pozisyon Kontrolü ve İşlem Mantığı
        if position > 0:
            # Kar Al / Zarar Durdur Kontrolleri
            pct_change = ((close - entry_price) / entry_price) * 100
            
            exit_reason = None
            if pct_change <= -stop_loss_pct:
                exit_reason = f"Stop-Loss Tetiklendi (-%{stop_loss_pct:.1f})"
            elif pct_change >= take_profit_pct:
                exit_reason = f"Kar Al Tetiklendi (+%{take_profit_pct:.1f})"
            elif sell_signal:
                exit_reason = "Sat Sinyali Oluştu"

            if exit_reason:
                # Satış işlemi
                revenue = position * close * (1 - commission_rate)
                profit = revenue - (position * entry_price)
                pnl_pct = ((close - entry_price) / entry_price) * 100
                cash += revenue
                
                trades.append({
                    "entry_date": entry_date.strftime("%Y-%m-%d") if hasattr(entry_date, 'strftime') else str(entry_date),
                    "exit_date": current_date.strftime("%Y-%m-%d") if hasattr(current_date, 'strftime') else str(current_date),
                    "entry_price": round(entry_price, 2),
                    "exit_price": round(close, 2),
                    "pnl_amount": round(profit, 2),
                    "pnl_pct": round(pnl_pct, 2),
                    "reason": exit_reason
                })
                position = 0
                entry_price = 0.0
                entry_date = None

        elif position == 0 and buy_signal:
            # Alış işlemi
            shares_to_buy = int(cash / (close * (1 + commission_rate)))
            if shares_to_buy > 0:
                cost = shares_to_buy * close * (1 + commission_rate)
                cash -= cost
                position = shares_to_buy
                entry_price = close
                entry_date = current_date

        # Gün sonu portföy toplam değeri
        current_portfolio_val = cash + (position * close)
        equity_curve.append({
            "Date": current_date,
            "Portfolio": round(current_portfolio_val, 2),
            "Benchmark": round(initial_capital * (close / df['Close'].iloc[30]), 2)
        })

    # Son günde açık pozisyon varsa kapat ve rapora ekle
    if position > 0:
        final_close = float(df['Close'].iloc[-1])
        revenue = position * final_close * (1 - commission_rate)
        profit = revenue - (position * entry_price)
        pnl_pct = ((final_close - entry_price) / entry_price) * 100
        cash += revenue
        trades.append({
            "entry_date": entry_date.strftime("%Y-%m-%d") if hasattr(entry_date, 'strftime') else str(entry_date),
            "exit_date": df.index[-1].strftime("%Y-%m-%d") if hasattr(df.index[-1], 'strftime') else str(df.index[-1]),
            "entry_price": round(entry_price, 2),
            "exit_price": round(final_close, 2),
            "pnl_amount": round(profit, 2),
            "pnl_pct": round(pnl_pct, 2),
            "reason": "Test Dönemi Sonu Pozisyon Kapatıldı"
        })

    # Performans İstatistikleri
    total_equity = cash
    total_return_pct = ((total_equity - initial_capital) / initial_capital) * 100
    
    first_close = float(df['Close'].iloc[30])
    last_close = float(df['Close'].iloc[-1])
    benchmark_return_pct = ((last_close - first_close) / first_close) * 100

    total_trades = len(trades)
    winning_trades = [t for t in trades if t['pnl_amount'] > 0]
    losing_trades = [t for t in trades if t['pnl_amount'] <= 0]
    
    win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0.0
    
    gross_profit = sum(t['pnl_amount'] for t in winning_trades)
    gross_loss = abs(sum(t['pnl_amount'] for t in losing_trades))
    profit_factor = round(gross_profit / (gross_loss + 1e-5), 2)

    # Max Drawdown Hesaplama
    equity_df = pd.DataFrame(equity_curve)
    if not equity_df.empty:
        peak = equity_df['Portfolio'].cummax()
        drawdown = (equity_df['Portfolio'] - peak) / peak * 100
        max_drawdown = round(abs(drawdown.min()), 2)
    else:
        max_drawdown = 0.0

    return {
        "initial_capital": initial_capital,
        "final_capital": round(total_equity, 2),
        "total_return_pct": round(total_return_pct, 2),
        "benchmark_return_pct": round(benchmark_return_pct, 2),
        "total_trades": total_trades,
        "winning_trades": len(winning_trades),
        "losing_trades": len(losing_trades),
        "win_rate": round(win_rate, 1),
        "profit_factor": profit_factor,
        "max_drawdown_pct": max_drawdown,
        "trades": trades,
        "equity_curve": equity_df
    }
