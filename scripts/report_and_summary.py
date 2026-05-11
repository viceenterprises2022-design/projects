import requests
import html

TOKEN = "8770565112:AAGy9q-BMWsgvU4RQUQDyeNXa282Vme9uG4"
CHAT_ID = "7246234100"

news_summary = """
<b>1. Trump Rejects Iran Peace Terms</b>
U.S. President Donald Trump rejected Iran's ceasefire proposal, labeling it "totally unacceptable."
<i>Why it matters:</i> Signals a breakdown in diplomacy, increasing the risk of prolonged conflict in the Middle East and sustained global energy market volatility.

<b>2. Oil Prices Surge to $105</b>
Brent crude jumped over 4% following the failure of U.S.-Iran peace talks.
<i>Why it matters:</i> Higher energy costs directly impact global inflation and transportation sectors, complicating central bank efforts to stabilize economies.

<b>3. Strait of Hormuz Blockade Continues</b>
Iran maintains its block on the critical oil transit route following maritime drone attacks.
<i>Why it matters:</i> Disrupts 20% of global oil supply, creating supply chain bottlenecks and increasing regional military tensions.

<b>4. AI Infrastructure Boom in Asia</b>
South Korean stocks hit record highs driven by aggressive data center and AI hardware investments.
<i>Why it matters:</i> Reinforces the dominance of the AI narrative in global capital markets and the strategic shift of manufacturing hubs toward AI-specialized infrastructure.

<b>5. Spirit Airlines Ceases Operations</b>
The low-cost carrier entered its second Chapter 11 bankruptcy in two years and stopped all flights.
<i>Why it matters:</i> Highlights the fragility of the travel sector under the pressure of rising fuel costs and geopolitical instability.

<b>6. Hungary’s 16-Year Orbán Era Ends</b>
Péter Magyar was sworn in as Prime Minister after a landslide victory over Viktor Orbán.
<i>Why it matters:</i> Represents a major shift in EU internal politics and could lead to significant changes in Hungary's relations with Brussels and its stance on the Ukraine-Russia conflict.

<b>7. Hantavirus Outbreak on Cruise Ship</b>
Passengers from the MV Hondius are disembarking in Tenerife under strict quarantine.
<i>Why it matters:</i> While the WHO says risk is low, it adds to the current travel sector woes and triggers health safety protocols across major tourist hubs.

<b>8. Keir Starmer Launches Political "Fightback"</b>
The UK PM is reframing EU relations as his government's defining mission after local election losses.
<i>Why it matters:</i> Suggests a potential "softening" of Brexit stances or a push for deeper UK-EU integration to bolster a struggling domestic economy.

<b>9. Macquarie Group Profit Rises 30%</b>
The financial giant reported FY26 net profit of $4.85 billion, beating estimates.
<i>Why it matters:</i> Demonstrates the resilience of diversified financial institutions in high-rate, volatile environments.

<b>10. Ted Turner Passes Away at 87</b>
The media mogul and philanthropist behind CNN has died.
<i>Why it matters:</i> Marks the end of an era for global broadcast news and 24-hour cable media, likely sparking reflections on the future of traditional news in the AI age.
"""

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    r = requests.post(url, json=payload)
    return r.json()

if __name__ == "__main__":
    send_to_telegram("<b>NEWS SUMMARY - MAY 11, 2026</b>\n" + news_summary)
