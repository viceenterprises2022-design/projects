import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def build_excel_model():
    wb = openpyxl.Workbook()
    default_sheet = wb.active
    wb.remove(default_sheet)

    font_family = "Calibri"
    
    # Fonts
    font_title = Font(name=font_family, size=16, bold=True, color="FFFFFF")
    font_section = Font(name=font_family, size=13, bold=True, color="1F4E78")
    font_header = Font(name=font_family, size=11, bold=True, color="FFFFFF")
    font_bold = Font(name=font_family, size=11, bold=True)
    font_italic = Font(name=font_family, size=9, italic=True, color="595959")
    font_regular = Font(name=font_family, size=11)
    
    # Fills
    fill_navy_dark = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    fill_navy_light = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
    fill_accent = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    fill_green_light = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    fill_gray_light = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    
    # Alignments
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")
    align_title = Alignment(horizontal="left", vertical="center", indent=1)

    # Borders
    thin_border_side = Side(style='thin', color='D9D9D9')
    border_all = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    
    border_double_bottom_side = Side(style='double', color='000000')
    border_thin_top_side = Side(style='thin', color='000000')
    border_total = Border(top=border_thin_top_side, bottom=border_double_bottom_side)

    # Helper function to auto-adjust column widths
    def autofit_columns(ws, min_width=12, padding=3):
        for col in ws.columns:
            max_len = 0
            for cell in col:
                val_str = str(cell.value or '')
                if val_str.startswith('='):
                    max_len = max(max_len, 10)
                else:
                    max_len = max(max_len, len(val_str))
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + padding, min_width)

    # -------------------------------------------------------------
    # SHEET 1: EXECUTIVE DASHBOARD
    # -------------------------------------------------------------
    ws1 = wb.create_sheet(title="Executive Dashboard")
    ws1.views.sheetView[0].showGridLines = True
    
    ws1.merge_cells("A1:G2")
    ws1["A1"] = "OMEGA V1 TOKEN RESELLER BUSINESS MODEL"
    ws1["A1"].font = font_title
    ws1["A1"].fill = fill_navy_dark
    ws1["A1"].alignment = align_title
    
    params = [
        ("Base Stock (1B packs):", 100),
        ("Packs Sold to Date:", 30),
        ("Landing Cost per 1M Tokens:", 0.11),
        ("Net Discount to Buyer:", 0.20),
        ("Average Block Price:", 30.00),
        ("Min Block Price (Gemini Flash):", 2.00),
        ("Max Block Price (GPT-4o/Claude):", 75.00)
    ]
    
    for idx, (label, val) in enumerate(params, 5):
        ws1.cell(row=idx, column=1, value=label).font = font_bold
        ws1.cell(row=idx, column=1).alignment = align_left
        
        cell_val = ws1.cell(row=idx, column=2, value=val)
        cell_val.font = font_regular
        cell_val.alignment = align_right
        
        if "Discount" in label:
            cell_val.number_format = "0.0%"
        elif "Price" in label or "Cost" in label:
            cell_val.number_format = "$#,##0.00"
        else:
            cell_val.number_format = "#,##0"
            
    ws1["D4"] = "Current Inventory State"
    ws1["D4"].font = font_section
    
    inv_data = [
        ("Total Base Stock (Tokens):", "=B5*1000000000"),
        ("Total Sold (Tokens):", "=B6*1000000000"),
        ("Remaining Inventory (Tokens):", "=B12-B13"),
        ("Remaining Inventory (1B packs):", "=B5-B6"),
        ("Total Landing Cost (Remaining):", "=B15*B7*1000")
    ]
    
    ws1["B12"] = "=B5*1000000000"
    ws1["B13"] = "=B6*1000000000"
    ws1["B14"] = "=B12-B13"
    ws1["B15"] = "=B5-B6"
    ws1["B16"] = "=B15*B7*1000"

    for idx, (label, formula) in enumerate(inv_data, 5):
        ws1.cell(row=idx, column=4, value=label).font = font_bold
        ws1.cell(row=idx, column=4).alignment = align_left
        
        cell_val = ws1.cell(row=idx, column=5, value=formula)
        cell_val.font = font_regular
        cell_val.alignment = align_right
        
        if "Tokens" in label:
            cell_val.number_format = "#,##0"
        elif "Cost" in label:
            cell_val.number_format = "$#,##0.00"
            cell_val.fill = fill_accent
        else:
            cell_val.number_format = "#,##0"

    ws1["A14"] = "Scenario Calculations Summary"
    ws1["A14"].font = font_section
    
    headers = ["Scenario (Block Size)", "Total Blocks (Remaining)", "Average Price / Block", "Total Gross Revenue", "Total Landing Cost", "Net Gross Profit", "Gross Margin %"]
    for col_idx, h in enumerate(headers, 1):
        cell = ws1.cell(row=16, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_navy_light
        cell.alignment = align_center
    ws1.row_dimensions[16].height = 25

    ws1["B17"] = "=B14/1000000"
    ws1["C17"] = "=B9"
    ws1["D17"] = "=B17*C17"
    ws1["E17"] = "=B17*B7"
    ws1["F17"] = "=D17-E17"
    ws1["G17"] = "=F17/D17"

    ws1["B18"] = "=B14/100000"
    ws1["C18"] = "=B9"
    ws1["D18"] = "=B18*C18"
    ws1["E18"] = "=B18*(B7/10)"
    ws1["F18"] = "=D18-E18"
    ws1["G18"] = "=F18/D18"

    scenarios = [
        ("Scenario A (1 Block = 1M Tokens)", "=B17", "=C17", "=D17", "=E17", "=F17", "=G17"),
        ("Scenario B (1 Block = 100k Tokens)", "=B18", "=C18", "=D18", "=E18", "=F18", "=G18")
    ]

    for r_idx, (label, blk, prc, rev, cogs, prof, pct) in enumerate(scenarios, 17):
        ws1.cell(row=r_idx, column=1, value=label).font = font_bold
        ws1.cell(row=r_idx, column=1).alignment = align_left
        ws1.cell(row=r_idx, column=1).border = border_all
        
        for c_idx, val in enumerate([blk, prc, rev, cogs, prof, pct], 2):
            cell = ws1.cell(row=r_idx, column=c_idx, value=val)
            cell.font = font_regular if c_idx != 6 else font_bold
            cell.alignment = align_right
            cell.border = border_all
            
            if c_idx == 2:
                cell.number_format = "#,##0"
            elif c_idx in [3, 4, 5, 6]:
                cell.number_format = "$#,##0.00"
                if c_idx == 6:
                    cell.fill = fill_green_light
            elif c_idx == 7:
                cell.number_format = "0.0%"
                cell.fill = fill_green_light

    autofit_columns(ws1, min_width=15)

    # -------------------------------------------------------------
    # SHEET 2: SCENARIO COMPARISON (70B REMAINING vs 1T CAP)
    # -------------------------------------------------------------
    ws2 = wb.create_sheet(title="Scenario Math Comparison")
    ws2.views.sheetView[0].showGridLines = True
    
    ws2.merge_cells("A1:G2")
    ws2["A1"] = "DETAILED MATHEMATICAL ANALYSIS BY BLOCK SIZE"
    ws2["A1"].font = font_title
    ws2["A1"].fill = fill_navy_dark
    ws2["A1"].alignment = align_title
    
    headers_s2 = ["Metric", "Scenario A (1 Block = 1M Tokens)", "Scenario B (1 Block = 100k Tokens)", "Formula / Explanation"]
    for col_idx, h in enumerate(headers_s2, 1):
        cell = ws2.cell(row=4, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_navy_light
        cell.alignment = align_center
    ws2.row_dimensions[4].height = 25

    metrics_data = [
        ("Block Size in Tokens", 1000000, 100000, "Scenario A: 1M Tokens/Block | Scenario B: 100k Tokens/Block"),
        ("Average Price per Block", "='Executive Dashboard'!B9", "='Executive Dashboard'!B9", "Blended target selling price per block"),
        ("Remaining Inventory (Tokens)", "='Executive Dashboard'!B14", "='Executive Dashboard'!B14", "70 Billion tokens remaining out of 100B stock"),
        ("Remaining Inventory (Blocks)", "=B7/B5", "=C7/C5", "Remaining tokens divided by block size"),
        ("Remaining Gross Revenue", "=B8*B6", "=C8*C6", "Remaining blocks * average price per block"),
        ("Remaining Landing Cost (COGS)", "=B8*('Executive Dashboard'!B7*B5/1000000)", "=C8*('Executive Dashboard'!B7*C5/1000000)", "Blocks * landing cost per block"),
        ("Remaining Gross Profit", "=B9-B10", "=C9-C10", "Gross revenue minus landing cost"),
        ("Remaining Gross Margin %", "=B11/B9", "=C11/C9", "Gross profit divided by gross revenue"),
        ("Max Scale Capacity (Tokens)", 1000000000000, 1000000000000, "1 Trillion tokens max capacity"),
        ("Max Capacity in Blocks", "=B13/B5", "=C13/C5", "1 Trillion tokens divided by block size"),
        ("Max Capacity Gross Revenue", "=B14*B6", "=C14*C6", "Max blocks * average price per block"),
        ("Max Capacity Landing Cost", "=B14*('Executive Dashboard'!B7*B5/1000000)", "=C14*('Executive Dashboard'!B7*C5/1000000)", "Max blocks * landing cost per block"),
        ("Max Capacity Gross Profit", "=B15-B16", "=C15-C16", "Max capacity gross profit"),
        ("Max Capacity Gross Margin %", "=B17/B15", "=C17/C15", "Max profit divided by max revenue")
    ]

    for idx, row_data in enumerate(metrics_data, 5):
        label, val_a, val_b, desc = row_data
        ws2.cell(row=idx, column=1, value=label).font = font_bold if "Revenue" in label or "Profit" in label or "Margin" in label else font_regular
        ws2.cell(row=idx, column=1).alignment = align_left
        ws2.cell(row=idx, column=1).border = border_all
        
        cell_a = ws2.cell(row=idx, column=2, value=val_a)
        cell_b = ws2.cell(row=idx, column=3, value=val_b)
        cell_desc = ws2.cell(row=idx, column=4, value=desc)
        
        cell_a.border = border_all
        cell_b.border = border_all
        cell_desc.border = border_all
        
        cell_a.alignment = align_right
        cell_b.alignment = align_right
        cell_desc.alignment = align_left
        cell_desc.font = font_italic
        
        is_currency = "Price" in label or "Revenue" in label or "Cost" in label or "Profit" in label
        is_pct = "Margin %" in label
        is_token = "Tokens" in label
        is_block = "Blocks" in label
        
        for c in [cell_a, cell_b]:
            if is_currency:
                c.number_format = "$#,##0.00"
                if "Profit" in label:
                    c.fill = fill_green_light
                    c.font = font_bold
            elif is_pct:
                c.number_format = "0.0%"
                c.fill = fill_green_light
                c.font = font_bold
            elif is_token or is_block:
                c.number_format = "#,##0"
                if "Remaining" in label or "Max" in label:
                    c.font = font_bold
            else:
                c.number_format = "#,##0"

    autofit_columns(ws2, min_width=18)

    # -------------------------------------------------------------
    # SHEET 3: OFFICIAL API PRICING MODELS (JUNE 2026)
    # -------------------------------------------------------------
    ws3 = wb.create_sheet(title="Official API Prices")
    ws3.views.sheetView[0].showGridLines = True
    
    ws3.merge_cells("A1:G2")
    ws3["A1"] = "OFFICIAL API PRICING MODELS - OPENAI, CLAUDE, & GEMINI"
    ws3["A1"].font = font_title
    ws3["A1"].fill = fill_navy_dark
    ws3["A1"].alignment = align_title
    
    headers_s3 = ["AI Provider", "Model Name", "Input Cost ($/1M)", "Output Cost ($/1M)", "Blended Cost ($/1M)*", "Reseller Price / 1M", "Gross Margin %"]
    for col_idx, h in enumerate(headers_s3, 1):
        cell = ws3.cell(row=4, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_navy_light
        cell.alignment = align_center
    ws3.row_dimensions[4].height = 25

    # Models data from the specified URLs
    official_models = [
        # OpenAI Models
        ("OpenAI", "GPT-5.5 Standard", 5.00, 30.00, "=C5*0.8+D5*0.2", 3.00, "=1-('Executive Dashboard'!B7/F5)"),
        ("OpenAI", "GPT-5.5 Pro", 30.00, 180.00, "=C6*0.8+D6*0.2", 20.00, "=1-('Executive Dashboard'!B7/F6)"),
        ("OpenAI", "GPT-5.4 Standard", 2.50, 15.00, "=C7*0.8+D7*0.2", 2.00, "=1-('Executive Dashboard'!B7/F7)"),
        ("OpenAI", "GPT-5.4 Mini", 0.75, 4.50, "=C8*0.8+D8*0.2", 0.60, "=1-('Executive Dashboard'!B7/F8)"),
        ("OpenAI", "GPT-5.4 Nano", 0.20, 1.25, "=C9*0.8+D9*0.2", 0.16, "=1-('Executive Dashboard'!B7/F9)"),
        
        # Claude Models
        ("Anthropic", "Claude Fable 5", 10.00, 50.00, "=C10*0.8+D10*0.2", 8.00, "=1-('Executive Dashboard'!B7/F10)"),
        ("Anthropic", "Claude Opus 4.8", 5.00, 25.00, "=C11*0.8+D11*0.2", 4.00, "=1-('Executive Dashboard'!B7/F11)"),
        ("Anthropic", "Claude Sonnet 4.6", 3.00, 15.00, "=C12*0.8+D12*0.2", 2.40, "=1-('Executive Dashboard'!B7/F12)"),
        ("Anthropic", "Claude Haiku 4.5", 1.00, 5.00, "=C13*0.8+D13*0.2", 0.80, "=1-('Executive Dashboard'!B7/F13)"),
        
        # Gemini Models
        ("Google", "Gemini 3.1 Pro Preview", 2.00, 12.00, "=C14*0.8+D14*0.2", 1.60, "=1-('Executive Dashboard'!B7/F14)"),
        ("Google", "Gemini 3.5 Flash", 1.50, 9.00, "=C15*0.8+D15*0.2", 1.20, "=1-('Executive Dashboard'!B7/F15)"),
        ("Google", "Gemini 3.1 Flash-Lite", 0.25, 1.50, "=C16*0.8+D16*0.2", 0.20, "=1-('Executive Dashboard'!B7/F16)"),
        ("Google", "Gemini 2.5 Flash-Lite", 0.10, 0.40, "=C17*0.8+D17*0.2", 0.08, "=1-('Executive Dashboard'!B7/F17)"),
    ]

    for idx, row_data in enumerate(official_models, 5):
        for col_idx, val in enumerate(row_data, 1):
            cell = ws3.cell(row=idx, column=col_idx, value=val)
            cell.font = font_regular
            cell.border = border_all
            
            if col_idx in [1, 2]:
                cell.alignment = align_left
            elif col_idx in [3, 4, 5, 6]:
                cell.alignment = align_right
                cell.number_format = "$#,##0.00"
            elif col_idx == 7:
                cell.alignment = align_right
                cell.number_format = "0.0%"
                cell.fill = fill_green_light
                cell.font = font_bold

    ws3["A19"] = "* Note: Blended Cost assumes 80% input and 20% output token split. Reseller Price / 1M is calculated at a 20% net discount compared to direct blended cost."
    ws3["A19"].font = font_italic

    autofit_columns(ws3, min_width=18)

    # -------------------------------------------------------------
    # SHEET 4: GTM SALES PIPELINE & CALCULATOR
    # -------------------------------------------------------------
    ws4 = wb.create_sheet(title="Interactive Sales Calculator")
    ws4.views.sheetView[0].showGridLines = True
    
    ws4.merge_cells("A1:D2")
    ws4["A1"] = "INTERACTIVE SALES PLANNING CALCULATOR"
    ws4["A1"].font = font_title
    ws4["A1"].fill = fill_navy_dark
    ws4["A1"].alignment = align_title

    ws4["A4"] = "Enter sales targets to dynamically calculate pipeline value."
    ws4["A4"].font = font_italic

    # Inputs Block
    ws4["A6"] = "Pipeline Inputs (Editable)"
    ws4["A6"].font = font_bold
    ws4["A6"].fill = fill_accent
    
    ws4["A7"] = "Target Blocks to Sell:"
    ws4["A7"].font = font_regular
    ws4["B7"] = 70000
    ws4["B7"].font = font_bold
    ws4["B7"].number_format = "#,##0"

    ws4["A8"] = "Blended Block Price ($):"
    ws4["A8"].font = font_regular
    ws4["B8"] = 30.00
    ws4["B8"].font = font_bold
    ws4["B8"].number_format = "$#,##0.00"

    ws4["A9"] = "Landing Cost per Block ($):"
    ws4["A9"].font = font_regular
    ws4["B9"] = "='Executive Dashboard'!B7"
    ws4["B9"].font = font_bold
    ws4["B9"].number_format = "$#,##0.00"

    ws4["A10"] = "Discount Offered to Buyer (%):"
    ws4["A10"].font = font_regular
    ws4["B10"] = "='Executive Dashboard'!B8"
    ws4["B10"].font = font_bold
    ws4["B10"].number_format = "0.0%"

    # Outputs Block
    ws4["C6"] = "Calculated Revenue & Profits"
    ws4["C6"].font = font_bold
    ws4["C6"].fill = fill_accent
    
    ws4["C7"] = "Total Gross Revenue (List Price):"
    ws4["C7"].font = font_regular
    ws4["D7"] = "=B7*B8"
    ws4["D7"].font = font_bold
    ws4["D7"].number_format = "$#,##0.00"

    ws4["C8"] = "Net Discount Value ($):"
    ws4["C8"].font = font_regular
    ws4["D8"] = "=D7*B10"
    ws4["D8"].font = font_bold
    ws4["D8"].number_format = "$#,##0.00"

    ws4["C9"] = "Net Revenue (After Discount):"
    ws4["C9"].font = font_regular
    ws4["D9"] = "=D7-D8"
    ws4["D9"].font = font_bold
    ws4["D9"].number_format = "$#,##0.00"

    ws4["C10"] = "Total Landing Cost (COGS):"
    ws4["C10"].font = font_regular
    ws4["D10"] = "=B7*B9"
    ws4["D10"].font = font_bold
    ws4["D10"].number_format = "$#,##0.00"

    ws4["C12"] = "Net Reseller Profit:"
    ws4["C12"].font = font_bold
    ws4["C12"].fill = fill_green_light
    ws4["D12"] = "=D9-D10"
    ws4["D12"].font = font_bold
    ws4["D12"].number_format = "$#,##0.00"
    ws4["D12"].fill = fill_green_light
    ws4["D12"].border = border_total

    ws4["C13"] = "Reseller Gross Margin %:"
    ws4["C13"].font = font_bold
    ws4["C13"].fill = fill_green_light
    ws4["D13"] = "=D12/D9"
    ws4["D13"].font = font_bold
    ws4["D13"].number_format = "0.0%"
    ws4["D13"].fill = fill_green_light
    ws4["D13"].border = border_total

    for r in range(6, 11):
        ws4.cell(row=r, column=1).border = border_all
        ws4.cell(row=r, column=2).border = border_all
        ws4.cell(row=r, column=3).border = border_all
        ws4.cell(row=r, column=4).border = border_all
        
    ws4.cell(row=12, column=3).border = border_all
    ws4.cell(row=12, column=4).border = border_all
    ws4.cell(row=13, column=3).border = border_all
    ws4.cell(row=13, column=4).border = border_all

    autofit_columns(ws4, min_width=25)

    filepath = "/home/vreddy1/Desktop/Projects/scripts/token-sale/token_sale_model.xlsx"
    wb.save(filepath)
    print(f"Excel model successfully generated at: {filepath}")

if __name__ == "__main__":
    build_excel_model()
