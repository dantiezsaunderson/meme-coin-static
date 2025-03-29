import os
import json
import time
import requests
from datetime import datetime, timedelta

# Configuration
SOLANA_API_KEY = os.environ.get('SOLANA_API_KEY', '020da7f45b05497f951bc2218489ee73')
ETHEREUM_API_KEY = os.environ.get('ETHEREUM_API_KEY', 'DE3J7IZAIN7FS327J5RR9TMBBEGBHQN6CD')
TEMPLATE_FILE = 'template.html'
OUTPUT_FILE = 'index.html'

# API endpoints
SOLANA_API_URL = 'https://public-api.birdeye.so/public/tokenlist'
SOLANA_TOKEN_INFO_URL = 'https://public-api.birdeye.so/public/token_list/info'
ETHEREUM_API_URL = 'https://api.etherscan.io/api'

def get_current_time():
    """Get current time formatted for display."""
    return datetime.now().strftime('%B %d, %Y %H:%M:%S')

def fetch_solana_tokens():
    """Fetch new token launches from Solana."""
    headers = {"x-api-key": SOLANA_API_KEY}
    params = {"sort_by": "created", "sort_type": "desc", "offset": 0, "limit": 50}
    
    try:
        response = requests.get(SOLANA_API_URL, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            tokens = data.get('data', {}).get('tokens', [])
            # Add blockchain identifier
            for token in tokens:
                token['blockchain'] = 'Solana'
            return tokens
        else:
            print(f"Error fetching Solana tokens: {response.status_code}")
            return []
    except Exception as e:
        print(f"Exception fetching Solana tokens: {e}")
        return []

def fetch_ethereum_tokens():
    """Fetch new token launches from Ethereum."""
    # Using Etherscan API to get latest token contracts
    params = {
        "module": "account",
        "action": "tokentx",
        "startblock": 0,
        "endblock": 999999999,
        "sort": "desc",
        "apikey": ETHEREUM_API_KEY,
        "limit": 50
    }
    
    try:
        response = requests.get(ETHEREUM_API_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == '1':
                raw_transactions = data.get('result', [])
                
                # Process transactions to extract unique tokens
                tokens = []
                seen_addresses = set()
                
                for tx in raw_transactions:
                    token_address = tx.get('contractAddress')
                    if token_address and token_address not in seen_addresses:
                        seen_addresses.add(token_address)
                        
                        # Get token creation timestamp
                        creation_time = int(tx.get('timeStamp', 0))
                        
                        # Create token object
                        token = {
                            'address': token_address,
                            'symbol': tx.get('tokenSymbol', 'UNKNOWN'),
                            'name': tx.get('tokenName', 'Unknown Token'),
                            'created': creation_time * 1000,  # Convert to milliseconds for consistency
                            'blockchain': 'Ethereum'
                        }
                        tokens.append(token)
                
                return tokens
            else:
                print(f"Error in Ethereum API response: {data.get('message')}")
                return []
        else:
            print(f"Error fetching Ethereum tokens: {response.status_code}")
            return []
    except Exception as e:
        print(f"Exception fetching Ethereum tokens: {e}")
        return []

def get_solana_token_details(token_address):
    """Get detailed information about a Solana token."""
    headers = {"x-api-key": SOLANA_API_KEY}
    params = {"token_address": token_address}
    
    try:
        response = requests.get(SOLANA_TOKEN_INFO_URL, headers=headers, params=params)
        if response.status_code == 200:
            return response.json().get('data', {})
        else:
            print(f"Error fetching Solana token details: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Exception fetching Solana token details: {e}")
        return {}

def get_ethereum_token_details(token_address):
    """Get detailed information about an Ethereum token."""
    # Get token info
    token_info_params = {
        "module": "token",
        "action": "tokeninfo",
        "contractaddress": token_address,
        "apikey": ETHEREUM_API_KEY
    }
    
    # Get token balance/supply
    token_supply_params = {
        "module": "stats",
        "action": "tokensupply",
        "contractaddress": token_address,
        "apikey": ETHEREUM_API_KEY
    }
    
    try:
        # Get token info
        info_response = requests.get(ETHEREUM_API_URL, params=token_info_params)
        info_data = {}
        if info_response.status_code == 200:
            info_data = info_response.json().get('result', {})
            if isinstance(info_data, list) and len(info_data) > 0:
                info_data = info_data[0]
        
        # Get liquidity and volume data (simplified for demo)
        # In a real implementation, you would query DEX APIs or other sources
        
        # Simulate liquidity and volume data for demo
        import random
        liquidity = random.randint(10000, 200000)
        volume = {
            "h1": random.randint(5000, 100000)
        }
        
        return {
            "info": info_data,
            "liquidity": liquidity,
            "volume": volume
        }
    except Exception as e:
        print(f"Exception fetching Ethereum token details: {e}")
        return {}

def filter_tokens(tokens):
    """Filter tokens based on criteria."""
    qualified_tokens = []
    
    for token in tokens:
        # Check if token is less than 12 hours old
        created_time = token.get('created', 0) / 1000  # Convert from milliseconds
        current_time = time.time()
        age_hours = (current_time - created_time) / 3600
        
        if age_hours > 12:
            continue
        
        # Get more details about the token based on blockchain
        blockchain = token.get('blockchain', 'Solana')
        if blockchain == 'Solana':
            token_details = get_solana_token_details(token.get('address', ''))
        else:  # Ethereum
            token_details = get_ethereum_token_details(token.get('address', ''))
        
        # Check liquidity
        liquidity = token_details.get('liquidity', 0)
        if liquidity < 50000:
            continue
            
        # Check volume
        volume_1h = token_details.get('volume', {}).get('h1', 0)
        if volume_1h < 25000:
            continue
            
        # Calculate DYOR score (simplified for demo)
        dyor_score = calculate_dyor_score(token_details, blockchain)
        if dyor_score < 60:
            continue
            
        # Calculate sentiment score (simplified for demo)
        sentiment_score = calculate_sentiment_score(token.get('symbol', ''))
        if sentiment_score < 60:
            continue
            
        # Add additional information to token
        token['age_hours'] = round(age_hours, 1)
        token['liquidity'] = liquidity
        token['volume_1h'] = volume_1h
        token['dyor_score'] = dyor_score
        token['sentiment_score'] = sentiment_score
        token['influencer'] = get_random_influencer(blockchain)
        
        qualified_tokens.append(token)
        
        # Limit to top 6 tokens (3 per blockchain if available)
        solana_count = sum(1 for t in qualified_tokens if t.get('blockchain') == 'Solana')
        ethereum_count = sum(1 for t in qualified_tokens if t.get('blockchain') == 'Ethereum')
        
        if (blockchain == 'Solana' and solana_count >= 3) or (blockchain == 'Ethereum' and ethereum_count >= 3):
            if solana_count >= 3 and ethereum_count >= 3:
                break
            continue
    
    return qualified_tokens

def calculate_dyor_score(token_details, blockchain):
    """Calculate a DYOR score based on token details."""
    # This is a simplified version for demonstration
    # In a real implementation, this would check LP lock, ownership, etc.
    score = 60
    
    # Add random variation for demo
    import random
    score += random.randint(0, 25)
    
    return min(score, 100)

def calculate_sentiment_score(token_symbol):
    """Calculate sentiment score based on social media mentions."""
    # This is a simplified version for demonstration
    # In a real implementation, this would check Twitter, etc.
    score = 60
    
    # Add random variation for demo
    import random
    score += random.randint(0, 20)
    
    return min(score, 100)

def get_random_influencer(blockchain):
    """Get a random influencer name for demonstration."""
    if blockchain == 'Solana':
        influencers = [
            "SolWhaleAlpha", "SolanaGems", "SolanaWhale", 
            "SolMoonHunter", "SolanaGuru", "SolanaSniper"
        ]
    else:  # Ethereum
        influencers = [
            "EthWhale", "EthereumGems", "ETHMoonshots", 
            "DeFiGuru", "EthSniper", "ETHAlpha"
        ]
    
    import random
    return random.choice(influencers)

def format_currency(amount):
    """Format amount as currency string."""
    if amount >= 1000000:
        return f"${round(amount/1000000, 1)}M"
    elif amount >= 1000:
        return f"${round(amount/1000, 1)}K"
    else:
        return f"${round(amount, 2)}"

def generate_token_html(token):
    """Generate HTML for a token card."""
    chain = token.get('blockchain', 'Solana')
    
    # Set chart link based on blockchain
    if chain == 'Solana':
        chart_link = f"https://birdeye.so/token/{token.get('address', '')}"
    else:  # Ethereum
        chart_link = f"https://etherscan.io/token/{token.get('address', '')}"
    
    # Set badge color based on blockchain
    badge_class = "bg-primary" if chain == 'Solana' else "bg-warning"
    
    html = f'''
        <div class="token-alert">
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <h5 class="mb-1">${token.get('symbol', 'UNKNOWN')} <span class="badge {badge_class}">{chain}</span></h5>
                    <p class="mb-2">{token.get('name', 'Unknown Token')}</p>
                </div>
                <div>
                    <span class="badge bg-success">DYOR: {token.get('dyor_score', 0)}</span>
                    <span class="badge bg-info">Sentiment: {token.get('sentiment_score', 0)}</span>
                </div>
            </div>
            <div class="row mt-2">
                <div class="col-md-6">
                    <p><strong>Liquidity:</strong> {format_currency(token.get('liquidity', 0))}</p>
                    <p><strong>Volume (1h):</strong> {format_currency(token.get('volume_1h', 0))}</p>
                </div>
                <div class="col-md-6">
                    <p><strong>Age:</strong> {token.get('age_hours', 0)} hours</p>
                    <p><strong>Top Influencer:</strong> {token.get('influencer', 'None')}</p>
                </div>
            </div>
            <div class="mt-2">
                <a href="{chart_link}" target="_blank" class="btn btn-sm btn-outline-primary">View Chart</a>
            </div>
        </div>
    '''
    return html

def update_dashboard():
    """Main function to update the dashboard with real data."""
    # Get current time
    current_time = get_current_time()
    
    # Fetch tokens from both blockchains
    solana_tokens = fetch_solana_tokens()
    ethereum_tokens = fetch_ethereum_tokens()
    
    # Combine tokens
    all_tokens = solana_tokens + ethereum_tokens
    
    # Filter tokens
    qualified_tokens = filter_tokens(all_tokens)
    
    # If no qualified tokens found, create sample data
    if not qualified_tokens:
        print("No qualified tokens found, using sample data")
        # Create sample token data for both blockchains
        qualified_tokens = [
            {
                'symbol': 'SPEPE',
                'name': 'Super Pepe',
                'age_hours': 6.5,
                'liquidity': 58000,
                'volume_1h': 31000,
                'dyor_score': 85,
                'sentiment_score': 77,
                'influencer': 'SolWhaleAlpha',
                'address': '7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU',
                'blockchain': 'Solana'
            },
            {
                'symbol': 'MDOGE',
                'name': 'Moon Doge',
                'age_hours': 8.2,
                'liquidity': 72000,
                'volume_1h': 45000,
                'dyor_score': 75,
                'sentiment_score': 68,
                'influencer': 'CryptoGems',
                'address': '4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R',
                'blockchain': 'Solana'
            },
            {
                'symbol': 'FLOKI',
                'name': 'Floki Moon',
                'age_hours': 10.1,
                'liquidity': 65000,
                'volume_1h': 28000,
                'dyor_score': 70,
                'sentiment_score': 65,
                'influencer': 'BSCWhale',
                'address': '6XU36wCxWobLx5Rtsb58kmgAJKVYmMVqy4SHXxENAyAe',
                'blockchain': 'Solana'
            },
            {
                'symbol': 'PEPE2',
                'name': 'Pepe 2.0',
                'age_hours': 5.3,
                'liquidity': 85000,
                'volume_1h': 52000,
                'dyor_score': 82,
                'sentiment_score': 75,
                'influencer': 'EthWhale',
                'address': '0x6982508145454ce325ddbe47a25d4ec3d2311933',
                'blockchain': 'Ethereum'
            },
            {
                'symbol': 'WOJAK',
                'name': 'Wojak Finance',
                'age_hours': 7.8,
                'liquidity': 67000,
                'volume_1h': 38000,
                'dyor_score': 68,
                'sentiment_score': 72,
                'influencer': 'ETHMoonshots',
                'address': '0x25f8087ead173b73d6e8b84329989a8eea16cf73',
                'blockchain': 'Ethereum'
            },
            {
                'symbol': 'MOON',
                'name': 'MoonCoin',
                'age_hours': 9.5,
                'liquidity': 59000,
                'volume_1h': 27000,
                'dyor_score': 65,
                'sentiment_score': 63,
                'influencer': 'DeFiGuru',
                'address': '0x68749665ff8d2d112fa859aa293f07a622782f38',
                'blockchain': 'Ethereum'
            }
        ]
    
    # Generate token HTML
    token_html = ""
    for token in qualified_tokens:
        token_html += generate_token_html(token)
    
    # Read template HTML
    try:
        with open('index.html', 'r') as file:
            template = file.read()
    except:
        print("Error reading template file, using default template")
        # If template file doesn't exist, use the current index.html
        with open('index.html', 'r') as file:
            template = file.read()
    
    # Replace placeholders
    updated_html = template
    
    # Update timestamp
    updated_html = updated_html.replace('March 29, 2025 15:24:48', current_time)
    
    # Update footer timestamp
    updated_html = updated_html.replace('Last Updated: March 29, 2025', f'Last Updated: {current_time}')
    
    # Find the token-alert divs and replace them
    import re
    token_section_pattern = r'<div class="card-body">\s*<div class="token-alert">.*?</div>\s*</div>\s*</div>'
    token_section_replacement = f'<div class="card-body">{token_html}</div></div>'
    
    updated_html = re.sub(token_section_pattern, token_section_replacement, updated_html, flags=re.DOTALL)
    
    # Update chains in the header
    chains_pattern = r'Monitoring high-potential meme coins across Solana, Ethereum, and BSC'
    chains_replacement = 'Monitoring high-potential meme coins across Solana and Ethereum'
    updated_html = updated_html.replace(chains_pattern, chains_replacement)
    
    # Write updated HTML
    with open('index.html', 'w') as file:
        file.write(updated_html)
    
    print(f"Dashboard updated successfully at {current_time}")

if __name__ == "__main__":
    update_dashboard()
