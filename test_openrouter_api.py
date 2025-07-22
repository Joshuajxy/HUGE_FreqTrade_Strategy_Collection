import requests
import os

# You can set OPENROUTER_API_KEY in the environment variable, or fill it in here.
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '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')
OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'
MODEL = 'openai/gpt-4.1'  # Modify as needed
# Read the full NASDAQ100 symbol list from file
with open('nasdaq100_symbols.txt', 'r', encoding='utf-8') as f:
    nasdaq100_symbols = [line.strip() for line in f if line.strip()]

QUESTION = (
    "You MUST use the following list of NASDAQ100 stock symbols (provided below) to generate your table. For each symbol, output a row in the table, even if you do not have data (in that case, fill with 'No Data'). DO NOT summarize, DO NOT skip any symbol, DO NOT provide any explanation or text outside the table."
    "\n\nNASDAQ100 SYMBOL LIST:\n" + ', '.join(nasdaq100_symbols) +
    "\n\nFor each symbol, strictly provide the following columns:"
    "\n- Symbol"
    "\n- Company Name"
    "\n- Comprehensive Score (1-10)"
    "\n- Estimated 30-day Change (%)"
    "\n- Confidence Level (High/Medium/Low)"
    "\n- Key Factors (up to 3)"
    "\n\nWhen analyzing, please consider:"
    "\n1. Technical indicators (such as price trend, volume, RSI, moving averages, etc.);"
    "\n2. Fundamentals (financial reports, revenue, profit, cash flow, debt);"
    "\n3. Industry trends (overall industry performance, market share, competitive advantage);"
    "\n4. Macroeconomic factors (interest rates, inflation, employment, etc.);"
    "\n5. Market sentiment (analyst ratings, institutional holdings, social media)."
    "\n\nAgain: Output a table with one row for EACH symbol in the provided list. If information is missing, fill with 'No Data'. DO NOT summarize. DO NOT skip. DO NOT explain outside the table."
)


def test_openrouter_api():
    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
    }
    data = {
        'model': MODEL,
        'messages': [
            {"role": "user", "content": QUESTION}
        ]
    }
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data, timeout=20)
        print('Status Code:', response.status_code)
        print('Response Content:', response.text)
        import json
        try:
            resp_json = response.json()
            print('JSON parsed successfully:', resp_json)
            # Save as json format for later analysis
            with open('model_raw_output.json', 'w', encoding='utf-8') as f:
                json.dump(resp_json, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print('JSON parsing failed:', e)
            # If parsing fails, still save the original text to the json file
            with open('model_raw_output.json', 'w', encoding='utf-8') as f:
                json.dump({'raw': response.text}, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print('Request exception:', e)

if __name__ == '__main__':
    test_openrouter_api()
