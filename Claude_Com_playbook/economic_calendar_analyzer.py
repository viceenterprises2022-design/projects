#!/usr/bin/env python3
"""
Economic Calendar Fetcher and Analyzer for Precious Metals Trading
Fetches data from TradingEconomics and analyzes impact on gold/silver
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

def fetch_calendar_from_web():
    """
    Fetch economic calendar using web_fetch tool
    Returns parsed calendar data
    """
    try:
        # Use Claude's web_fetch tool
        url = "https://tradingeconomics.com/calendar"
        print(f"Fetching calendar from {url}...")
        
        # This will be replaced with actual web_fetch call
        # For now, return structure for integration
        return {
            'status': 'success',
            'url': url,
            'fetch_method': 'web_fetch'
        }
    except Exception as e:
        print(f"Error fetching calendar: {e}")
        return None

def categorize_event_impact(event_name: str, country: str) -> str:
    """
    Categorize event impact on precious metals
    
    Returns: 'HIGH', 'MEDIUM', or 'LOW'
    """
    event_lower = event_name.lower()
    
    # High impact events (Very likely to move metals significantly)
    high_impact_keywords = [
        'cpi', 'consumer price', 'inflation rate',
        'ppi', 'producer price',
        'fomc', 'interest rate decision', 'federal funds rate',
        'nfp', 'non-farm payroll', 'payrolls',
        'employment situation', 'unemployment rate',
        'gdp', 'gross domestic product',
        'pce', 'personal consumption',
        'fed chair', 'powell', 'jerome powell',
        'retail sales',
        'ism manufacturing', 'ism services', 'ism pmi'
    ]
    
    # Medium impact events (Can move metals moderately)
    medium_impact_keywords = [
        'durable goods', 'factory orders',
        'consumer confidence', 'consumer sentiment',
        'housing starts', 'building permits', 'home sales', 'home prices',
        'fed speak', 'fed member', 'fomc member',
        'jobless claims', 'continuing claims',
        'trade balance', 'current account',
        'ecb', 'european central bank',
        'boe', 'bank of england',
        'boj', 'bank of japan',
        'treasury auction'
    ]
    
    # US events get priority for precious metals
    if country == 'United States' or 'US' in country:
        for keyword in high_impact_keywords:
            if keyword in event_lower:
                return 'HIGH'
        for keyword in medium_impact_keywords:
            if keyword in event_lower:
                return 'MEDIUM'
    
    # Major central bank events even if not US
    if any(word in event_lower for word in ['rate decision', 'monetary policy', 'interest rate']):
        if any(bank in event_lower for bank in ['ecb', 'boe', 'boj', 'rba', 'boc']):
            return 'MEDIUM'
    
    return 'LOW'

def analyze_metals_correlation(event_name: str) -> Dict:
    """
    Analyze how event typically correlates with gold/silver prices
    
    Returns dict with direction, description, and volatility
    """
    event_lower = event_name.lower()
    
    # Event correlation patterns
    correlations = {
        'cpi': {
            'direction': '⬆️ Strong Positive',
            'description': 'Higher inflation → supports gold as inflation hedge and store of value',
            'volatility': 'Very High',
            'expected_move': {'gold': '30-60 points', 'silver': '1.00-2.00'},
            'interpretation': 'Above forecast = Bullish | Below forecast = Bearish'
        },
        'ppi': {
            'direction': '⬆️ Positive',
            'description': 'Leading inflation indicator → impacts inflation expectations for gold',
            'volatility': 'High',
            'expected_move': {'gold': '20-40 points', 'silver': '0.60-1.20'},
            'interpretation': 'Above forecast = Bullish | Below forecast = Bearish'
        },
        'fomc': {
            'direction': '↔️ Variable (Policy-Dependent)',
            'description': 'Dovish stance = Bullish gold | Hawkish stance = Bearish gold',
            'volatility': 'Very High',
            'expected_move': {'gold': '40-80 points', 'silver': '1.50-3.00'},
            'interpretation': 'Rate cut = Bullish | Rate hike = Bearish | Hawkish hold = Bearish'
        },
        'nfp': {
            'direction': '⬇️ Negative',
            'description': 'Strong jobs → Fed hawkish → bearish gold | Weak jobs → Fed dovish → bullish gold',
            'volatility': 'Very High',
            'expected_move': {'gold': '25-50 points', 'silver': '0.80-1.50'},
            'interpretation': 'Above forecast = Bearish | Below forecast = Bullish'
        },
        'employment': {
            'direction': '⬇️ Negative',
            'description': 'Strong employment → supports higher rates → bearish for gold',
            'volatility': 'Very High',
            'expected_move': {'gold': '25-50 points', 'silver': '0.80-1.50'},
            'interpretation': 'Above forecast = Bearish | Below forecast = Bullish'
        },
        'gdp': {
            'direction': '⬇️ Slight Negative',
            'description': 'Strong growth → higher yields and rates → generally bearish for gold',
            'volatility': 'Medium',
            'expected_move': {'gold': '15-30 points', 'silver': '0.40-0.80'},
            'interpretation': 'Above forecast = Bearish | Below forecast = Bullish'
        },
        'retail sales': {
            'direction': '↔️ Mixed',
            'description': 'Strong sales → growth (yields ↑) vs inflation (gold ↑) → complex reaction',
            'volatility': 'Medium-High',
            'expected_move': {'gold': '15-35 points', 'silver': '0.50-1.00'},
            'interpretation': 'Context-dependent: Check inflation and Fed stance'
        },
        'pce': {
            'direction': '⬆️ Strong Positive',
            'description': 'Fed\'s preferred inflation gauge → directly impacts policy expectations',
            'volatility': 'Very High',
            'expected_move': {'gold': '30-60 points', 'silver': '1.00-2.00'},
            'interpretation': 'Above forecast = Bullish | Below forecast = Bearish'
        },
        'jobless claims': {
            'direction': '⬆️ Slight Positive',
            'description': 'Rising claims → labor softening → dovish Fed → bullish gold',
            'volatility': 'Low-Medium',
            'expected_move': {'gold': '10-20 points', 'silver': '0.30-0.60'},
            'interpretation': 'Above forecast = Bullish | Below forecast = Bearish'
        }
    }
    
    # Check which correlation applies
    for key, value in correlations.items():
        if key in event_lower:
            return value
    
    # Default for unknown events
    return {
        'direction': '↔️ Variable',
        'description': 'Impact depends on context and market conditions',
        'volatility': 'Low-Medium',
        'expected_move': {'gold': '5-15 points', 'silver': '0.20-0.50'},
        'interpretation': 'Monitor reaction, no strong historical pattern'
    }

def generate_trading_strategy(impact: str, correlation: Dict, event_time: str) -> Dict:
    """
    Generate trading strategy recommendations based on event impact
    
    Returns dict with pre-event, during-event, and post-event strategies
    """
    if impact == 'HIGH':
        return {
            'pre_event': [
                '⚠️ Reduce position size to 25-50% of normal',
                '🛑 Tighten stops or close positions entirely',
                '❌ Cancel pending orders',
                f"📏 Prepare for {correlation['expected_move']['gold']} range expansion in gold",
                '💼 Move existing stops to breakeven if possible'
            ],
            'during_event': [
                '⏸️ STAND ASIDE - Do not trade',
                '👀 Observe initial reaction direction and volume',
                '⚡ Let algorithms exhaust the first move (0-15 minutes)',
                '📊 Watch for fake-outs and whipsaws',
                '🎯 Note key levels being tested'
            ],
            'post_event': [
                '✅ Trade the confirmation, not the headline',
                '🔍 Look for failed breakouts to fade',
                '⏰ Wait 15-30 minutes for structure clarity',
                '📈 Require 3+ confirmation signals before entry',
                '📐 Define new support/resistance based on post-event structure'
            ],
            'risk_advisory': f'🔴 HIGH VOLATILITY EVENT - Expect {correlation["volatility"].lower()} volatility'
        }
    
    elif impact == 'MEDIUM':
        return {
            'pre_event': [
                '⚠️ Reduce position size to 75% of normal',
                '👁️ Be aware but can maintain core positions',
                '❌ Avoid aggressive new positions immediately before release'
            ],
            'during_event': [
                '⏸️ Pause new entries during release (0-5 minutes)',
                '👀 Monitor for unexpected reactions'
            ],
            'post_event': [
                '✅ Resume normal trading after 10-15 minutes',
                '🔍 Watch for surprises that could shift bias'
            ],
            'risk_advisory': f'🟡 MEDIUM VOLATILITY EVENT - Monitor closely'
        }
    
    else:  # LOW
        return {
            'pre_event': [
                '✅ Trade normally',
                '👁️ Monitor for any surprises'
            ],
            'during_event': [
                '✅ Normal trading can continue'
            ],
            'post_event': [
                '✅ Standard post-trade analysis'
            ],
            'risk_advisory': '🟢 NORMAL VOLATILITY - Standard trading conditions'
        }

def analyze_money_supply_impact(event_name: str, forecast: Optional[str], previous: Optional[str]) -> str:
    """
    Analyze how event affects money supply and Fed policy expectations
    """
    event_lower = event_name.lower()
    
    if 'cpi' in event_lower or 'ppi' in event_lower or 'pce' in event_lower:
        return """
Money Supply Implication:
• Hot inflation (above forecast) → Fed maintains restrictive policy → Higher rates longer → Headwind for gold
• Cool inflation (below forecast) → Fed can ease sooner → Lower rates ahead → Tailwind for gold
• Persistent inflation → May trigger QT acceleration → Tighter money supply → Gold pressure
• Disinflation trend → Opens door for rate cuts → Easier money supply → Gold supportive
"""
    
    elif 'fomc' in event_lower or 'interest rate' in event_lower:
        return """
Money Supply Implication:
• Rate cut → Expansionary → Lower opportunity cost for gold → Bullish
• Rate hike → Contractionary → Higher opportunity cost for gold → Bearish
• QE announcement → Direct money supply expansion → Very bullish for gold
• QT announcement → Direct money supply contraction → Bearish for gold
• Dovish forward guidance → Future easing expected → Gold supportive
• Hawkish forward guidance → Future tightening expected → Gold pressure
"""
    
    elif 'nfp' in event_lower or 'employment' in event_lower or 'payroll' in event_lower:
        return """
Money Supply Implication:
• Strong jobs → Fed can stay restrictive → Delays rate cuts → Bearish for gold
• Weak jobs → Fed may need to ease → Accelerates rate cuts → Bullish for gold
• Wage growth high → Inflationary pressure → Complicates Fed easing → Mixed for gold
• Labor market slack → Disinflationary → Enables Fed easing → Gold supportive
"""
    
    elif 'gdp' in event_lower:
        return """
Money Supply Implication:
• Strong GDP → Fed less likely to ease → Restrictive policy continues → Bearish for gold
• Weak GDP → Fed more likely to ease → Accommodative shift → Bullish for gold
• Above-trend growth → Reduces recession fears → Less safe-haven demand → Gold pressure
• Below-trend growth → Increases recession fears → Safe-haven demand → Gold supportive
"""
    
    elif 'retail sales' in event_lower:
        return """
Money Supply Implication:
• Strong sales → Economic resilience → Fed stays hawkish → Bearish for gold
• Weak sales → Economic softening → Fed may ease → Bullish for gold
• Consumer spending drives 70% of GDP → Critical for Fed policy path
"""
    
    else:
        return """
Money Supply Implication:
• Impact depends on how data affects Fed policy expectations
• Watch for comments from Fed officials following the release
• Consider in context of overall economic trends
"""

def format_calendar_for_playbook(events: List[Dict], today: datetime) -> str:
    """
    Format calendar analysis for integration into trading playbook
    """
    # Separate events by impact level
    high_impact = [e for e in events if e.get('impact') == 'HIGH']
    medium_impact = [e for e in events if e.get('impact') == 'MEDIUM']
    
    output = "📅 ECONOMIC CALENDAR IMPACT\n\n"
    output += "**Today's Key Events:**\n\n"
    
    # High impact events
    if high_impact:
        output += "[HIGH IMPACT] 🔴\n"
        for event in high_impact:
            correlation = analyze_metals_correlation(event['event'])
            strategy = generate_trading_strategy('HIGH', correlation, event.get('time', 'TBD'))
            money_supply = analyze_money_supply_impact(event['event'], event.get('forecast'), event.get('previous'))
            
            output += f"⏰ {event.get('time', 'TBD')} - {event['event']}\n"
            
            if event.get('forecast') or event.get('previous'):
                output += f"   📊 Forecast: {event.get('forecast', 'N/A')} | Previous: {event.get('previous', 'N/A')}\n"
            
            output += f"   💥 Impact Level: VERY HIGH\n"
            output += f"   📈 Expected Move: Gold {correlation['expected_move']['gold']}, Silver {correlation['expected_move']['silver']}\n"
            output += f"   \n"
            output += f"   Metals Correlation: {correlation['direction']}\n"
            output += f"   {correlation['description']}\n"
            output += f"   {correlation['interpretation']}\n"
            output += f"   \n"
            output += f"   {money_supply}\n"
            output += f"   Trading Strategy:\n"
            output += f"   ⚠️ PRE-EVENT:\n"
            for item in strategy['pre_event']:
                output += f"      {item}\n"
            output += f"   \n"
            output += f"   ⏸️ DURING EVENT:\n"
            for item in strategy['during_event']:
                output += f"      {item}\n"
            output += f"   \n"
            output += f"   ✅ POST-EVENT:\n"
            for item in strategy['post_event']:
                output += f"      {item}\n"
            output += f"\n"
    
    # Medium impact events
    if medium_impact:
        output += "[MEDIUM IMPACT] 🟡\n"
        for event in medium_impact[:2]:  # Limit to 2 for brevity
            correlation = analyze_metals_correlation(event['event'])
            output += f"⏰ {event.get('time', 'TBD')} - {event['event']}\n"
            output += f"   💥 Impact: Medium\n"
            output += f"   📈 Expected Move: Gold {correlation['expected_move']['gold']}\n"
            output += f"   \n"
            output += f"   Strategy: Monitor for {correlation['volatility'].lower()} volatility, "
            output += f"react to confirmed moves\n\n"
    
    if not high_impact and not medium_impact:
        output += "🟢 No major market-moving events scheduled for today\n"
        output += "   Strategy: Normal trading conditions, standard position sizing\n\n"
    
    return output


# Example usage structure
def main():
    """
    Main function to demonstrate calendar analysis
    """
    print("Economic Calendar Analyzer for Precious Metals")
    print("=" * 60)
    
    # This would be called with actual calendar data
    sample_events = [
        {
            'time': '8:30 AM ET',
            'country': 'United States',
            'event': 'Consumer Price Index (CPI)',
            'forecast': '2.8% YoY',
            'previous': '2.7% YoY',
            'impact': 'HIGH'
        },
        {
            'time': '2:00 PM ET',
            'country': 'United States',
            'event': 'FOMC Meeting Minutes',
            'forecast': '-',
            'previous': '-',
            'impact': 'HIGH'
        }
    ]
    
    # Generate formatted output
    today = datetime.now()
    formatted = format_calendar_for_playbook(sample_events, today)
    print(formatted)

if __name__ == "__main__":
    main()
