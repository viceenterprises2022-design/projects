import sys
import os
import json

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the original script
import market_analysis_v3 as ma

# Mock the console and Rich objects to capture output or avoid errors
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

# We want to capture the final report
class CapturingConsole(Console):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output = []
    
    def print(self, *args, **kwargs):
        # Simplistic capture
        import io
        f = io.StringIO()
        temp_console = Console(file=f, force_terminal=False, width=100)
        temp_console.print(*args, **kwargs)
        self.output.append(f.getvalue())

# Replace the console in the original module
capturing_console = CapturingConsole()
ma.console = capturing_console

def run_headless():
    ma.init_db()
    
    results = []
    for sym in ["NIFTY", "BANKNIFTY"]:
        try:
            print(f"Running analysis for {sym}...")
            # result = (sym, q, oi_raw, res, final_signal, final_score)
            result = ma.run_analysis(sym)
            if result:
                ma.display_dashboard(*result)
                # Store the captured output for this symbol
                results.append("".join(capturing_console.output))
                capturing_console.output = [] # Reset for next
            else:
                results.append(f"Failed to run analysis for {sym}")
        except Exception as e:
            results.append(f"Error analyzing {sym}: {str(e)}")
            import traceback
            traceback.print_exc()

    # Join results and print to stdout
    final_report = "\n" + "="*80 + "\n"
    final_report += "MARKET ANALYSIS REPORT\n"
    final_report += "="*80 + "\n"
    final_report += "\n".join(results)
    
    print(final_report)

if __name__ == "__main__":
    run_headless()
